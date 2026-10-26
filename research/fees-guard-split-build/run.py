"""Reproduce the Linux Fees baseline, then compile PR74's one-file guard split.

Only acquisition has networking. Captured programs are not compiler inputs.
Every failed command and both raw outputs are retained without normalization.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tomllib

P = Path(__file__).resolve().parent
SOURCE_FILE = 'programs/pump-fees/src/types.rs'
OLD = b'        if buf.len() < 8 || &buf[..8] != Self::DISCRIMINATOR { return Err(ProgramError::InvalidAccountData.into()); }\n'
NEW = b'        if buf.len() < 8 { return Err(ProgramError::InvalidAccountData.into()); }\n        if &buf[..8] != Self::DISCRIMINATOR { return Err(ProgramError::InvalidAccountData.into()); }\n'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def read(path):
    return json.loads(path.read_bytes())


def split_guard(raw):
    # Restrict replacement to FeeConfig; similar account implementations remain unchanged.
    prefix, body = raw.split(b'impl AccountDeserialize for FeeConfig {', 1)
    end = body.index(b'    fn try_deserialize_unchecked(')
    checked, suffix = body[:end], body[end:]
    require(checked.count(OLD) == 1, 'FeeConfig guard changed or already split')
    return prefix + b'impl AccountDeserialize for FeeConfig {' + checked.replace(OLD, NEW, 1) + suffix


def source_hashes(root, expected):
    actual = {p.relative_to(root).as_posix(): file_sha(p) for p in root.rglob('*') if p.is_file()}
    require(actual == expected, 'Source file set or hashes differ')
    return actual


def source_members():
    policy, expected = read(P / 'policy.json'), read(P / 'source-inputs.json')
    require(file_sha(P / 'source.tar.gz') == policy['source']['archive_sha256'], 'Source archive changed')
    require(file_sha(P / 'proposal.patch') == policy['proposal']['sha256'], 'Proposal patch changed')
    require(len(expected) == policy['source']['tracked_input_count'] == 26, 'Wrong source count')
    files = {}
    with tarfile.open(P / 'source.tar.gz', 'r:gz') as archive:
        for member in archive:
            path = PurePosixPath(member.name)
            require(member.isfile() and not path.is_absolute() and '..' not in path.parts and
                    '\\' not in member.name and member.name in expected and member.name not in files,
                    'Unexpected source member')
            files[member.name] = archive.extractfile(member).read()
    require({k: sha(v) for k, v in files.items()} == expected, 'Source archive members differ')
    patch = (P / 'proposal.patch').read_bytes()
    require(b'-' + OLD in patch and b'+' + NEW.replace(b'\n', b'\n+', 1) in patch,
            'Replacement differs from the proposed patch')
    return files


def raw_record(path):
    return dict(bytes=path.stat().st_size, sha256=file_sha(path))


def require_baseline(path, policy):
    actual = raw_record(path)
    require(actual == policy['baseline'], 'Fresh baseline differs; split build must not start')
    return actual


class Commands:
    def __init__(self, folder, label):
        self.folder = folder
        self.path = folder / (label + '-commands.json')
        self.rows = []

    def run(self, label, argv, *, cwd=None, env=None, timeout=1200):
        row = dict(label=label, argv=[str(x) for x in argv], cwd=str(cwd) if cwd else None,
                   environment=env, started_at=datetime.now(timezone.utc).isoformat())
        self.rows.append(row)
        save(self.path, self.rows)
        try:
            result = subprocess.run(row['argv'], cwd=cwd, env=env, capture_output=True, timeout=timeout)
            row['exit'] = result.returncode
            stdout, stderr = result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            row['exit'] = None
            stdout, stderr = error.stdout or b'', error.stderr or b''
        for stream, raw in [('stdout', stdout), ('stderr', stderr)]:
            path = self.folder / (label + '.' + stream + '.log')
            path.write_bytes(raw)
            row[stream] = dict(file=path.name, bytes=len(raw), sha256=sha(raw))
        row['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(self.path, self.rows)
        require(row['exit'] == 0, label + ' failed; outputs retained')
        return stdout


def environment(phase, offline=True):
    run, compiler = Path('/gate/run'), Path('/gate/run/toolchains/v1.44')
    return {'HOME': str(run / 'home'), 'PATH': str(compiler / 'rust/bin') + ':' + str(compiler / 'llvm/bin') + ':/usr/bin:/bin',
        'LANG': 'C', 'LC_ALL': 'C', 'CARGO_HOME': str(run / 'cargo-home'),
        'CARGO_TARGET_DIR': str(run / 'baseline-target'), 'CARGO_NET_OFFLINE': 'true' if offline else 'false',
        'CARGO_TERM_COLOR': 'never', 'CARGO_INCREMENTAL': '0',
        'RUSTC': str(compiler / 'rust/bin/rustc'), 'RUSTDOC': str(compiler / 'rust/bin/rustdoc'),
        'CARGO_TARGET_SBF_SOLANA_SOLANA_RUSTFLAGS': '-Zremap-cwd-prefix=',
        'CC': str(compiler / 'llvm/bin/clang'), 'AR': str(compiler / 'llvm/bin/llvm-ar'),
        'OBJDUMP': str(compiler / 'llvm/bin/llvm-objdump'), 'OBJCOPY': str(compiler / 'llvm/bin/llvm-objcopy'),
        'RUSTC_WRAPPER': '/gate/driver/rustc-wrapper.py', 'FEES_PROBE_PHASE': phase}


def inside(phase):
    root = Path('/gate'); evidence = root / 'evidence'; source = root / 'input/source'
    commands = Commands(evidence, phase)
    env = environment(phase, offline=phase != 'fetch')
    policy = read(P / 'policy.json')
    expected = read(root / ('split-source-inputs.json' if phase == 'split' else 'driver/source-inputs.json'))
    save(evidence / (phase + '-source-before.json'), source_hashes(source, expected))
    cargo = '/gate/run/toolchains/v1.44/rust/bin/cargo'
    manifest = str(source / policy['source']['manifest'])
    if phase == 'fetch':
        commands.run('fetch-locked', [cargo, 'fetch', '--manifest-path', manifest, '--locked'], cwd=source, env=env)
    else:
        if phase == 'split':
            commands.run('split-clean-root', [cargo, 'clean', '--manifest-path', manifest, '-p',
                         'pump-fun-fees-candidate', '--target', 'sbf-solana-solana'], cwd=source, env=env)
        commands.run(phase + '-build', [cargo, 'build', '--manifest-path', manifest, '--release',
            '--target', 'sbf-solana-solana', '--locked', '--offline', '--verbose', '--config',
            'profile.release.strip="debuginfo"'], cwd=source, env=env, timeout=1800)
        artifact = root / 'run/baseline-target/sbf-solana-solana/release/pump_fees_candidate.so'
        copied = evidence / (phase + '.unstripped.so')
        require(not copied.exists(), 'Refuse to overwrite output')
        shutil.copyfile(artifact, copied)
        commands.run(phase + '-strip', ['/gate/run/toolchains/v1.52/llvm/bin/llvm-objcopy', '--strip-all',
                     str(copied), str(evidence / (phase + '.stripped.so'))], cwd=source, env=env)
    save(evidence / (phase + '-source-after.json'), source_hashes(source, expected))


def registry_inputs(root):
    lock = tomllib.loads((root / 'input/source/Cargo.lock').read_text())
    expected = {(p['name'], p['version']): p['checksum'] for p in lock['package'] if p.get('source', '').startswith('registry+')}
    require(not any(p.get('source', '').startswith('git+') for p in lock['package']), 'Unaccounted Git dependency')
    rows = []
    for path in sorted((root / 'run/cargo-home/registry/cache').glob('*/*.crate')):
        keys = [key for key in expected if path.name == key[0] + '-' + key[1] + '.crate']
        require(len(keys) == 1, 'Unexpected registry archive')
        key = keys[0]
        require(file_sha(path) == expected[key], 'Registry checksum differs')
        rows.append(dict(name=key[0], version=key[1], sha256=expected[key], bytes=path.stat().st_size))
    require({(r['name'], r['version']) for r in rows} == set(expected) and len(rows) == len(expected),
            'Incomplete or duplicate locked registry archives')
    return rows


def outer(output):
    require(platform.system() == 'Linux' and platform.machine() == 'x86_64', 'Use a Linux x86_64 runner')
    root = output.resolve(); require(not root.exists(), 'Fresh output directory required')
    evidence = root / 'evidence'; evidence.mkdir(parents=True)
    commands = Commands(evidence, 'host')
    state = dict(status='STARTED', source_changed_files=[], program_executions=0, target_inputs_mounted=False)
    policy = read(P / 'policy.json')
    try:
        driver = root / 'driver'; driver.mkdir()
        for name in ('run.py', 'rustc-wrapper.py', 'test_inputs.py', 'policy.json', 'source-inputs.json', 'proposal.patch', 'source.tar.gz', 'LICENSE'):
            shutil.copyfile(P / name, driver / name); shutil.copyfile(P / name, evidence / name)
        (driver / 'rustc-wrapper.py').chmod(0o755)
        source = root / 'input/source'
        for name, raw in source_members().items():
            dest = source / name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(raw)
        for name in ('home', 'cargo-home', 'toolchains'):
            (root / 'run' / name).mkdir(parents=True, exist_ok=True)
        tools = {}
        for kind, version in [('compile', 'v1.44'), ('strip', 'v1.52')]:
            spec = policy[kind]; archive = root / (version + '.tar.bz2')
            commands.run('download-' + version, ['curl', '--fail', '--location', '--connect-timeout', '30',
                '--max-time', '600', '--retry', '3', '--retry-delay', '5', '--retry-max-time', '900',
                '--output', str(archive), spec['archive_url']], timeout=1550)
            require(raw_record(archive) == dict(bytes=spec['archive_bytes'], sha256=spec['archive_sha256']), 'Wrong tool archive')
            destination = root / 'run/toolchains' / version; destination.mkdir()
            # The archive is fully hash-bound first. Python's data filter confines links and rejects special files.
            with tarfile.open(archive, 'r:bz2') as stream:
                stream.extractall(destination, filter='data')
            identities = spec['selected_sha256'] if kind == 'compile' else {'llvm/bin/llvm-objcopy': spec['objcopy_sha256']}
            for name, digest in identities.items():
                require(file_sha(destination / name) == digest, 'Installed tool identity differs')
                tools[version + '/' + name] = raw_record(destination / name)
        save(evidence / 'tool-identities.json', tools)
        image = policy['container']['image']
        commands.run('pull-image', ['docker', 'pull', '--platform', 'linux/amd64', image], timeout=900)
        inspected = commands.run('inspect-image', ['docker', 'image', 'inspect', image])
        image_row, = json.loads(inspected)
        require(image in image_row['RepoDigests'], 'Pulled image digest differs')
        def phase(name, network):
            return commands.run('container-' + name, ['docker', 'run', '--rm', '--network', network, '--read-only',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,exec,nosuid,nodev,size=1g',
                '--mount', 'type=bind,source=' + str(root) + ',target=/gate',
                '--mount', 'type=bind,source=' + str(source) + ',target=/gate/input/source,readonly',
                '--mount', 'type=bind,source=' + str(driver) + ',target=/gate/driver,readonly',
                '--mount', 'type=bind,source=' + str(root / 'run/toolchains') + ',target=/gate/run/toolchains,readonly',
                '--entrypoint', 'python3', image, '/gate/driver/run.py', '--inside', name], timeout=2100)
        phase('fetch', 'bridge')
        dependencies = registry_inputs(root); save(evidence / 'registry-before.json', dependencies)
        phase('baseline', 'none')
        state['baseline'] = require_baseline(evidence / 'baseline.stripped.so', policy)
        save(evidence / 'observation.json', state)
        changed = source / SOURCE_FILE; before = changed.read_bytes(); after = split_guard(before)
        changed.write_bytes(after)
        expected = read(driver / 'source-inputs.json'); expected[SOURCE_FILE] = sha(after)
        source_hashes(source, expected)
        save(root / 'split-source-inputs.json', expected); save(evidence / 'split-source-inputs.json', expected)
        (evidence / 'split-types.rs').write_bytes(after)
        state['source_changed_files'] = [SOURCE_FILE]
        phase('split', 'none')
        state['split'] = raw_record(evidence / 'split.stripped.so')
        state['split_raw_equals_baseline'] = state['split'] == state['baseline']
        require(read(evidence / 'baseline-rustc-argv.json') == read(evidence / 'split-rustc-argv.json'), 'Root compiler arguments differ')
        require(registry_inputs(root) == dependencies, 'Registry archives changed')
        for name, identity in tools.items():
            require(raw_record(root / 'run/toolchains' / name) == identity, 'Tool changed during build')
        state.update(status='COMPLETED', identical_root_compiler_arguments=True, registry_archives_verified=len(dependencies))
    except Exception as error:
        state.update(status='FAILED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        save(evidence / 'observation.json', state)
    print(json.dumps(state, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--inside', choices=('fetch', 'baseline', 'split'))
    args = parser.parse_args()
    if args.inside:
        inside(args.inside)
    else:
        require(args.output is not None, 'Output required')
        outer(args.output)
