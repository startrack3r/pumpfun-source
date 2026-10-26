"""Compile two small block-order variants with pinned v1.37 llc, offline in Docker."""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import platform
import subprocess
import tarfile
import uuid

P = Path(__file__).resolve().parent
IMAGE = 'solanafoundation/solana-verifiable-build@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467'
IMAGE_ID = 'sha256:8a1c7e411dda3083f89fc82e9fbcbc57cfffed615853f11c124ef3df1443978f'
URL = 'https://github.com/anza-xyz/platform-tools/releases/download/v1.37/platform-tools-linux-x86_64.tar.bz2'
ARCHIVE_SHA = '8d5153589dbe19635affe937663cf4555a7e69a62d91ab4a1df064aaa8d5f066'
ARCHIVE_BYTES = 362756282
TOOLS = '/tools/platform'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def member_path(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,
            'Nonrelative archive member')
    return path.as_posix()


def inputs():
    """Same named CFG/instructions, changing only textual basic-block order."""
    prefix = 'target triple = "sbf"\n\ndeclare void @sink(ptr)\n\ndefine void @guard(ptr %out, i64 %n, i64 %total, i64 %remaining) {\n'
    blocks = {
        'entry': '''entry:
  %zero = icmp eq i64 %n, 0
  %over = icmp ugt i64 %n, %total
  %bad = or i1 %zero, %over
  br i1 %bad, label %initial_error, label %remaining_check
''',
        'remaining_check': '''remaining_check:
  %under = icmp ult i64 %remaining, %n
  br i1 %under, label %underflow_error, label %success
''',
        'initial_error': '''initial_error:
  store i64 86, ptr %out, align 8
  call void @sink(ptr %out)
  ret void
''',
        'success': '''success:
  %new_remaining = sub i64 %remaining, %n
  store i64 %new_remaining, ptr %out, align 8
  call void @sink(ptr %out)
  ret void
''',
        'underflow_error': '''underflow_error:
  store i64 86, ptr %out, align 8
  call void @sink(ptr %out)
  ret void
'''}
    orders = {
        'far-error': ['entry', 'remaining_check', 'initial_error', 'success', 'underflow_error'],
        'near-error': ['entry', 'remaining_check', 'underflow_error', 'initial_error', 'success']}
    return {name: (prefix + '\n'.join(blocks[b] for b in order) + '}\n').encode()
            for name, order in orders.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'Use a Linux x86_64 runner')
    root = args.output.resolve()
    require(not root.exists(), 'Fresh output required')
    evidence = root / 'evidence'
    evidence.mkdir(parents=True)
    source = root / 'inputs'
    source.mkdir()
    (evidence / 'probe.py').write_bytes(Path(__file__).read_bytes())
    state = dict(status='STARTED', observed_at=datetime.now(timezone.utc).isoformat(), commands=[],
                 image=IMAGE, network='none', original_program_inputs=False,
                 original_source_recovered=False, program_transactions=0)
    name = 'startrack3r-branch-layout-' + uuid.uuid4().hex[:12]
    container_started = False

    def run(label, command, required=True, timeout=180):
        try:
            result = subprocess.run(command, capture_output=True, timeout=timeout)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = None, error.stdout or b'', error.stderr or b''
        record = dict(label=label, command=command, returncode=code)
        for stream, raw in [('stdout', stdout), ('stderr', stderr)]:
            filename = label + '.' + stream + '.log'
            (evidence / filename).write_bytes(raw)
            record[stream] = dict(file=filename, bytes=len(raw), sha256=sha(raw))
        state['commands'].append(record)
        save(evidence / 'observation.json', state)
        require(not required or code == 0, label + ' failed; outputs retained')
        return stdout, stderr, code

    try:
        for variant, raw in inputs().items():
            (source / (variant + '.ll')).write_bytes(raw)
            (evidence / (variant + '.ll')).write_bytes(raw)
        archive = root / 'platform-tools.tar.bz2'
        run('download', ['curl', '--fail', '--location', '--connect-timeout', '30', '--max-time', '600',
                         '--output', str(archive), URL], timeout=650)
        with archive.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        require(archive.stat().st_size == ARCHIVE_BYTES and digest == ARCHIVE_SHA, 'Wrong archive')
        selected = {}
        with tarfile.open(archive, 'r|bz2') as tar:
            for member in tar:
                path = member_path(member.name)
                if path in ('llvm/bin/llc', 'llvm/bin/llvm-objdump', 'version.md'):
                    require(member.isfile(), 'Nonregular selected member')
                    require(path not in selected, 'Duplicate selected member')
                    raw = tar.extractfile(member).read()
                    selected[path] = dict(bytes=len(raw), sha256=sha(raw), archive_member=member.name)
                    if path == 'version.md':
                        (evidence / 'version.md').write_bytes(raw)
        save(evidence / 'selected-members.json', selected)
        require(set(selected) == {'llvm/bin/llc', 'llvm/bin/llvm-objdump', 'version.md'}, 'Missing tools')
        save(evidence / 'archive.json', dict(url=URL, bytes=ARCHIVE_BYTES, sha256=digest, selected=selected))
        run('pull-image', ['docker', 'pull', '--platform', 'linux/amd64', IMAGE], timeout=600)
        raw, _, _ = run('image-inspect', ['docker', 'image', 'inspect', IMAGE])
        inspected, = json.loads(raw)
        require(inspected['Id'] == IMAGE_ID and IMAGE in inspected['RepoDigests'], 'Wrong image')
        container_started = True
        run('start', ['docker', 'run', '--rm', '--detach', '--name', name, '--network', 'none',
            '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--tmpfs', '/tools:rw,exec,nosuid,nodev,size=2g', '--tmpfs', '/tmp:rw,nosuid,nodev,size=128m',
            '--mount', 'type=bind,source=' + str(archive) + ',target=/input/platform.tar.bz2,readonly',
            '--mount', 'type=bind,source=' + str(source) + ',target=/input/ir,readonly',
            '--entrypoint', 'sleep', IMAGE, '1800'])
        run('mkdir', ['docker', 'exec', name, 'mkdir', '-p', TOOLS])
        # Only three digest-bound regular members are extracted into the disposable tmpfs.
        run('install', ['docker', 'exec', name, 'tar', '--no-same-owner', '--no-same-permissions',
            '-xjf', '/input/platform.tar.bz2', '-C', TOOLS,
            *[row['archive_member'] for row in selected.values()]], timeout=300)
        for i, (path, identity) in enumerate(selected.items()):
            raw, _, _ = run(f'installed-{i}', ['docker', 'exec', name, 'sha256sum', TOOLS + '/' + path])
            require(raw.decode().split()[0] == identity['sha256'], 'Installed member changed')
        run('llc-version', ['docker', 'exec', name, TOOLS + '/llvm/bin/llc', '--version'])
        run('llc-libraries', ['docker', 'exec', name, 'ldd', TOOLS + '/llvm/bin/llc'])
        for variant in inputs():
            arguments = ['-mtriple=sbf', '-mcpu=generic', '-mattr=+solana', '-O3', '-filetype=obj',
                '-print-isel-input', '-print-before=finalize-isel',
                '-print-after=branch-folder,block-placement,sbf-mi-pemit-peephole',
                '/input/ir/' + variant + '.ll', '-o', '/tmp/' + variant + '.o']
            run(variant + '-compile', ['docker', 'exec', name, TOOLS + '/llvm/bin/llc', *arguments])
            run(variant + '-disassembly', ['docker', 'exec', name, TOOLS + '/llvm/bin/llvm-objdump',
                                         '-dr', '/tmp/' + variant + '.o'])
            run(variant + '-copy', ['docker', 'cp', name + ':/tmp/' + variant + '.o', str(evidence / (variant + '.o'))])
        state['status'] = 'COMPILED'
    except Exception as error:
        state.update(status='FAILED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        if container_started:
            _, _, status = run('cleanup', ['docker', 'stop', '--time', '1', name], required=False)
            state['cleanup_returncode'] = status
        save(evidence / 'observation.json', state)
    print(json.dumps(dict(status=state['status'], commands=len(state['commands']))))


if __name__ == '__main__':
    main()
