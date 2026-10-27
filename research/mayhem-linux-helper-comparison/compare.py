"""Compare two retained builds with the frozen helper method and independent gain checks."""
import ast
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys

DARWIN = "repro/identity-audit/2026-10-25/mayhem-v154"
LINUX = "repro/mayhem/linux-v154-recovery"
ORIGINAL = "evidence/original/mayhem/deployed.so"
RUN = LINUX + "/results/run-40293434354"
PARENT = "research/mayhem-sysroot-object-provenance"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path
    return module


def frozen_comparison(repo):
    """Keep the parent's definitions and replace only its local build-path table.

    Top-level path discovery and the script's writing entrypoint are not executed.
    The complete Darwin function ledger must reproduce the previously published
    result, including failures, raw bytes and pointer/call evidence.
    """
    path = repo / DARWIN / "match_helpers.py"
    tree = ast.parse(path.read_bytes(), filename=str(path))
    definitions = [n for n in tree.body
                   if isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef))]
    function, = [n for n in definitions if isinstance(n, ast.FunctionDef) and n.name == "analyze"]
    assignments = [n for n in function.body if isinstance(n, ast.Assign) and
                   len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "builds"]
    assignment, = assignments
    assignment.value = ast.Name(id="BUILDS", ctx=ast.Load())
    module = ast.fix_missing_locations(ast.Module(body=definitions, type_ignores=[]))
    namespace = dict(ROOT=repo / DARWIN, REPO=repo, BUILDS={
        "darwin": (repo / DARWIN / "build-01/candidate.so", repo / DARWIN / "build-01/unstripped.so"),
        "linux": (repo / RUN / "candidate.so", repo / RUN / "unstripped.so")})
    exec(compile(module, str(path), "exec"), namespace)
    result = namespace["analyze"]()
    # Canonicalize report path spelling only; no ELF or instruction bytes change.
    identities = [result["original"]] + [b[key] for b in result["builds"].values()
                                          for key in ("candidate", "symbol_source")]
    for identity in identities:
        identity["path"] = identity["path"].replace("\\", "/")
    prior = json.loads((repo / DARWIN / "helper-results.json").read_bytes())["builds"]["v154"]
    for key in ("functions", "summary", "candidate", "symbol_source"):
        if result["builds"]["darwin"][key] != prior[key]:
            raise ValueError("Frozen Darwin baseline differs: " + key)
    return result


def family(row):
    # Presentation/cohort matching only. These names do not label original functions.
    return tuple(re.sub(r"17h[0-9a-f]{16}E$", "E", n) for n in row["names"])


def raw_ranges(rows):
    return {(m["original_start"], f["bytes"]) for f in rows for m in f["matches"]
            if m["inferred_function_entry"] and m["next_entry_equals_window_end"] and m["raw_byte_equality"]}


def pointer_entries(obj, a):
    text, rels, calls, boundaries = a.context(obj)
    pointers = {}
    for row in rels:
        if row["type"] != 8 or row["symbol_index"] != 0:
            continue
        address = row["address"]
        sections = [s for s in obj.sections if s["flags"] & 2 and s["type"] != 8
                    and s["addr"] <= address and address + 8 <= s["addr"] + s["size"]]
        a.elf.require(len(sections) == 1, "relocation target has no unique allocated section")
        section, = sections
        at = section["offset"] + address - section["addr"]
        if section["name"] == ".text":
            if address not in boundaries or obj.data[at] != 0x18:
                continue
            raw = a.elf.checked_slice(obj.data, at, 16)
            target = struct.unpack_from("<I", raw, 4)[0] | struct.unpack_from("<I", raw, 12)[0] << 32
            encoding = "relocated LDDW immediate"
        else:
            raw = a.elf.checked_slice(obj.data, at, 8)
            stored, = struct.unpack("<Q", raw)
            if stored & 0xffffffff:
                continue
            target = stored >> 32
            encoding = "stored generic-v0 high-word pointer; low word zero"
        if target in boundaries:
            pointers.setdefault(target, []).append(dict(relocation=row, file_offset=at,
                section=section["name"], raw_hex=raw.hex(), encoding=encoding))
    entry_address, = struct.unpack_from("<Q", obj.data, 24)
    entries = set(calls) | set(pointers)
    if entry_address in boundaries:
        entries.add(entry_address)
    return dict(text=text, relocations=rels, calls=calls, pointers=pointers,
                entries=sorted(entries), instruction_boundaries=boundaries)


def window_evidence(obj, start, size, ctx, a):
    text = ctx["text"]
    address = text["addr"] + start - text["offset"]
    end = address + size
    following = next((x for x in ctx["entries"] if x > address), None)
    refs = lambda where: dict(direct_calls=ctx["calls"].get(where, []),
                              relocated_code_pointers=ctx["pointers"].get(where, []))
    overlap = a.overlapping(ctx["relocations"], address, end)
    return dict(file_offset=start, bytes=size, sha256=a.elf.digest(obj.data[start:start + size]),
        address=address, end_address=end, next_inferred_entry=following,
        start_evidence=refs(address), end_evidence=refs(end),
        complete_inferred_window=address in ctx["entries"] and following == end,
        loader_relocation_overlaps=overlap)


def returned_words(raw):
    """Decode the fixed two-LDDW/EXIT pattern without executing instructions."""
    if (len(raw) != 40 or raw[:4] != b"\x18\0\0\0" or raw[8:12] != b"\0" * 4 or
        raw[16:20] != b"\x18\x01\0\0" or raw[24:28] != b"\0" * 4 or
        raw[32:] != b"\x95" + b"\0" * 7):
        raise ValueError("not the two-constant return pattern")
    values = [struct.unpack_from("<I", raw, at + 4)[0] |
              struct.unpack_from("<I", raw, at + 12)[0] << 32 for at in (0, 16)]
    return {f"r{i}": f"0x{value:016x}" for i, value in enumerate(values)}


def literal_delta(before, after, a):
    a.elf.require(len(before) == len(after), "different body lengths")
    changes = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    call_words = {at + i for at, op, reg, off, _ in a.instructions(before)
                  if (op, reg, off) == (0x85, 0x10, 0) and after[at:at + 4] == before[at:at + 4]
                  for i in range(4, 8)}
    return dict(different_byte_offsets=changes, only_internal_call_displacements=bool(changes) and
                set(changes) <= call_words,
                changed_instructions=[dict(offset=i, darwin_hex=before[i:i + 8].hex(),
                    linux_hex=after[i:i + 8].hex()) for i in sorted({n // 8 * 8 for n in changes})])


def raw_callees(code, linux_start, original_start, linux, capture, functions, ctx, a):
    rows = []
    for offset, op, reg, off, immediate in a.instructions(code):
        if (op, reg, off) != (0x85, 0x10, 0):
            continue
        target = linux_start + offset + 8 + immediate * 8
        original_target = original_start + offset + 8 + immediate * 8
        symbols = [f for f in functions if f["offset"] == target]
        extents = {f["bytes"] for f in symbols}
        a.elf.require(len(extents) == 1, "gain callee has no unique symbol extent")
        size, = extents
        body = a.elf.checked_slice(linux, target, size)
        original_body = a.elf.checked_slice(capture.data, original_target, size)
        rows.append(dict(instruction_offset=offset, instruction_hex=code[offset:offset + 8].hex(),
            linux_target=target, original_target=original_target, bytes=size,
            candidate_names=sorted({f["symbol"] for f in symbols}),
            linux_sha256=a.elf.digest(body), original_sha256=a.elf.digest(original_body),
            raw_equal=body == original_body, original_window=original_target))
    return rows


def analyze(repo):
    a = load_module(repo / PARENT / "analyze.py", "sysroot_boundaries")
    v = a.elf
    comparison = frozen_comparison(repo)
    groups = {h: b["functions"] for h, b in comparison["builds"].items()}
    v.require(Counter(map(family, groups["darwin"])) == Counter(map(family, groups["linux"])),
              "helper selection families differ")
    saved = load_module(repo / LINUX / "verify_saved.py", "saved_linux_evidence")
    provenance = saved.verify(repo / LINUX, repo)
    frozen = json.loads((repo / DARWIN / "frozen-source.json").read_bytes())
    recorded = json.loads((repo / LINUX / "inputs.json").read_bytes())["source_sha256"]
    v.require({"programs/mayhem/" + k: value for k, value in frozen.items()} == recorded,
              "recorded source sets differ")
    capture = v.Elf((repo / ORIGINAL).read_bytes())
    ctx = pointer_entries(capture, a)
    data = dict(darwin=(repo / DARWIN / "build-01/candidate.so").read_bytes(),
                linux=(repo / RUN / "candidate.so").read_bytes())
    linux_symbols = a.functions(v.Elf((repo / RUN / "unstripped.so").read_bytes()))
    old_raw, new_raw = raw_ranges(groups["darwin"]), raw_ranges(groups["linux"])
    gains = []
    for name in sorted(set(map(family, groups["linux"]))):
        linux = [f for f in groups["linux"] if family(f) == name]
        darwin = [f for f in groups["darwin"] if family(f) == name]
        added = raw_ranges(linux) - raw_ranges(darwin)
        if not added:
            continue
        windows = [window_evidence(capture, start, size, ctx, a) for start, size in sorted(added)]
        v.require(all(w["complete_inferred_window"] and not w["loader_relocation_overlaps"]
                      for w in windows), "raw gain lacks independent boundary/relocation support")
        links = []
        for lf in linux:
            lb = data["linux"][lf["candidate_start"]:lf["candidate_start"] + lf["bytes"]]
            for df in darwin:
                db = data["darwin"][df["candidate_start"]:df["candidate_start"] + df["bytes"]]
                row = dict(linux_start=lf["candidate_start"], darwin_start=df["candidate_start"],
                           **literal_delta(db, lb, a))
                if any("type_id" in n for n in lf["names"]):
                    row["linux_return_constants"] = returned_words(lb)
                    row["darwin_return_constants"] = returned_words(db)
                links.append(row)
        edges = []
        for lf in linux:
            code = data["linux"][lf["candidate_start"]:lf["candidate_start"] + lf["bytes"]]
            for start, size in sorted(added):
                if capture.data[start:start + size] == code:
                    edges.append(dict(linux_start=lf["candidate_start"], original_start=start,
                        calls=raw_callees(code, lf["candidate_start"], start, data["linux"],
                                          capture, linux_symbols, ctx, a)))
        v.require({edge["original_start"] for edge in edges} == {start for start, _ in added},
                  "raw gain has no equal linked body")
        gains.append(dict(symbol_family=list(name), linux_symbols=[dict(names=f["names"],
            start=f["candidate_start"], bytes=f["bytes"], raw_sha256=f["raw_sha256"]) for f in linux],
            darwin_symbols=[dict(names=f["names"], start=f["candidate_start"], bytes=f["bytes"],
                                raw_sha256=f["raw_sha256"]) for f in darwin],
            captured_windows=windows, cross_host_deltas=links, outgoing_calls=edges,
            association="all equal-body alternatives retained; no unique original type attribution"))
    targets = {(c["original_target"], c["bytes"]) for g in gains
               for edge in g["outgoing_calls"] for c in edge["calls"]}
    findings = dict(method_counts={h: b["summary"] for h, b in comparison["builds"].items()},
        distinct_raw_capture_ranges=dict(darwin=len(old_raw), linux=len(new_raw),
                                         gained=sorted(new_raw - old_raw), lost=sorted(old_raw - new_raw)),
        raw_gain_families=gains,
        direct_callee_windows=[window_evidence(capture, start, size, ctx, a)
                               for start, size in sorted(targets)],
        linux_negatives=[dict(names=f["names"], start=f["candidate_start"], bytes=f["bytes"],
                             raw_sha256=f["raw_sha256"]) for f in groups["linux"] if not f["matches"]],
        linux_artifact_verification=provenance, recorded_source_inputs_equal=len(recorded),
        linux_builds_executed_here=0, target_executions=0, selected_artifacts_changed=False,
        scope="Two retained full-distribution recipes; not compiler-only or sysroot-only causality.")
    return comparison, findings
