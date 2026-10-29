"""Parse saved compiler dumps without compiling or executing the target."""
import hashlib
import re

HEADER = re.compile(rb'^(?:; |# )?\*\*\* IR Dump [^\r\n]+', re.M)
BLOCK = re.compile(r'^(?:\d+B)?[ \t]*bb\.(\d+)[^\r\n]*:', re.M)
SENTINEL = '-9223372036854775782'


def require(value, message):
    if not value:
        raise ValueError(message)


def machine_blocks(text):
    headers = list(BLOCK.finditer(text))
    end = text.index('# End machine code')
    return {int(m[1]): text[m.start():headers[i + 1].start() if i + 1 < len(headers) else end]
            for i, m in enumerate(headers)}


def ir_borrow_order(text):
    calls = list(re.finditer(r'^  (?:tail )?call void @_ZN19solana_account_info11AccountInfo15try_borrow_data', text, re.M))
    require(len(calls) == 1, 'IR borrow call census')
    labels = list(re.finditer(r'^([\w.$-]+):[^\r\n]*', text, re.M))
    j = max(j for j, label in enumerate(labels) if label.start() < calls[0].start())
    label, following = labels[j], labels[j + 1]
    body = text[label.start():following.start()]
    cmp = re.search(r'(%\d+) = icmp (eq|ne) i64 [^\r\n]*, ' + SENTINEL, body)
    require(cmp is not None, 'IR borrow sentinel comparison')
    branch = re.search(r'br i1 ' + re.escape(cmp[1]) + r', label %(\d+), label %(\d+)', body)
    if branch:
        success = branch[1 if cmp[2] == 'eq' else 2]
        form = 'direct-' + cmp[2]
    else:
        select = re.search(r'(%\d+) = select i1 ' + re.escape(cmp[1]) + r', i64 (\d+), i64 (\d+)', body)
        require(select is not None, 'IR select/switch predicate')
        require('switch i64 ' + select[1] + ',' in body, 'IR switch consumes selected discriminant')
        value = select[2 if cmp[2] == 'eq' else 3]
        target = re.search(r'i64 ' + value + r', label %(\d+)', body)
        require(target is not None, 'IR select/switch successor')
        success = target[1]
        form = 'select-switch-' + cmp[2]
    return dict(borrow_block=label[1], next_block=following[1], success_block=success,
                form=form, success_is_next=(success == following[1])), body, text[following.start():labels[j + 2].start()]


def analyze(raw):
    headers = list(HEADER.finditer(raw))
    snapshots = []
    machine = []
    ir_orders = []
    for i, m in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(raw)
        body = raw[m.start():end]
        row = dict(index=i, header=m[0].decode(), offset=m.start(), end=end,
                   bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        text = body.decode()
        if '# Machine code for function' in text:
            blocks = machine_blocks(text)
            borrow = [b for b in blocks.values() if 'try_borrow_data' in b]
            require(len(borrow) == 1, f'borrow block census at snapshot {i}')
            branch = [line.strip() for line in borrow[0].splitlines() if 'JNE_rr' in line or 'JEQ_rr' in line]
            require(len(branch) == 1 and 'JNE_rr' in branch[0] and SENTINEL in borrow[0],
                    f'borrow predicate at snapshot {i}')
            row.update(block_count=len(blocks), borrow_branch=branch[0])
            machine.append((row, blocks, borrow[0]))
        else:
            order, body, following = ir_borrow_order(text)
            row['ir_borrow_order'] = order
            ir_orders.append((row, body, following))
        snapshots.append(row)
    require(len(snapshots) == 392 and len(machine) == 116, 'complete snapshot census')
    require(len(ir_orders) == 276 and
            [r['ir_borrow_order']['success_is_next'] for r, _, _ in ir_orders] == [False] * 17 + [True] * 259,
            'IR success-adjacency boundary')
    earlier, before_body, before_following = ir_orders[16]
    later, after_body, after_following = ir_orders[17]
    require('Before SimplifyCFGPass' in earlier['header'] and 'After SimplifyCFGPass' in later['header'],
            'IR adjacency change pass')
    require([line.strip() for line in before_following.splitlines()[1:] if line.strip()] == ['br label %313'],
            'pre-SimplifyCFG intervening forwarding block')
    first, blocks, borrow = machine[0]
    require(first['index'] == 276 and '(finalize-isel)' in first['header'] and 'Before' in first['header'],
            'first captured machine stage')
    require('%bb.26' in borrow and 'JMP %bb.25' in borrow, 'first branch successors')
    require('%ir-block.232' in blocks[25] and '%ir-block.236' in blocks[26], 'successor IR identities')
    require('From$LT$solana_program_error..ProgramError' in blocks[26], 'error successor conversion')
    preceding = snapshots[first['index'] - 1]
    ir = raw[preceding['offset']:preceding['end']].decode()
    start = ir.rindex('\n225:', 0, ir.index('try_borrow_data'))
    finish = ir.index('\n232:', start)
    ir_borrow = ir[start:finish]
    require('(verify)' in preceding['header'] and 'After' in preceding['header'], 'last captured IR stage')
    require('%227 = icmp eq i64 %226, ' + SENTINEL in ir_borrow and
            'br i1 %227, label %232, label %236' in ir_borrow, 'IR equality and successors')
    selected = []
    for row, bs, bb in machine:
        if '(branch-folder)' in row['header'] or '(block-placement)' in row['header']:
            tail = [v for v in bs.values() if '%ir-block.541' in v.splitlines()[0]]
            require(len(tail) == 1, 'tail block census')
            selected.append(dict(**row, borrow_block=bb, tail_block=tail[0],
                                 block62=bs.get(62), block_order=list(bs)))
    require([r['block_count'] for r in selected] == [87, 85, 84, 82], 'late phase block counts')
    require('$r6 = LDD_V1 $r10, -1304' in selected[0]['tail_block'], 'pre-folder inline reload')
    require(all('$r6 = LDD_V1 $r10, -1304' not in r['tail_block'] for r in selected[1:]),
            'folder removes reload from final block')
    require('JMP %bb.62' in selected[-1]['tail_block'] and
            '$r6 = LDD_V1 $r10, -1304' in selected[-1]['block62'], 'placed shared reload')
    return dict(raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                snapshot_count=len(snapshots), machine_snapshot_count=len(machine),
                ir_adjacency_boundary=dict(before=dict(**earlier, borrow_body=before_body, following_block=before_following),
                                           after=dict(**later, borrow_body=after_body, following_block=after_following)),
                last_ir=dict(**preceding, borrow_block=ir_borrow),
                first_machine=dict(**first, borrow_block=borrow,
                                   equality_successor=blocks[25], inequality_successor=blocks[26]),
                late_stages=selected, snapshots=snapshots)
