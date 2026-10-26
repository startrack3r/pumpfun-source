"""Capture compiler stages while requiring candidate11's exact raw output.

Only dependency acquisition has network access. No captured executable is an input.
Raw compiler output is preserved without padding, rewriting or normalization.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
import tarfile
import tomllib
import uuid

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[1]
SOURCE_COMMIT = '17e99434af5ead3e989c08f32af33609821d0bc0'
SOURCE_URL = 'https://codeload.github.com/metaplex-foundation/mpl-token-metadata/tar.gz/' + SOURCE_COMMIT
SOURCE_SHA256 = 'a6a3d4d133c01877cfd3f5bb09bf1759d1c9139d924684f5790c0e08542dd092'
PINS = {
    'upstream-source-manifest.json': '55b0a2f46b574974d3cc35a72dce347537d250794464feb72d4f3cf968c55860',
    'source-manifest.json': 'a63e2a387aec93418e7f6cf20e59e8e1c5257c7e8961ba4f73c6fbc1bb63c045',
    'source.patch': 'fa954f23beae6c00eca4589e0208bf85a7d4dff185f18ff7863c629b12dd809c',
}
IMAGE = 'solanafoundation/solana-verifiable-build@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467'
IMAGE_ID = 'sha256:8a1c7e411dda3083f89fc82e9fbcbc57cfffed615853f11c124ef3df1443978f'
TOOLS_URL = 'https://github.com/anza-xyz/platform-tools/releases/download/v1.37/platform-tools-linux-x86_64.tar.bz2'
TOOLS_SHA256 = '8d5153589dbe19635affe937663cf4555a7e69a62d91ab4a1df064aaa8d5f066'
TOOLS_BYTES = 362756282
DRIVER_SHA256 = 'e7d221509c0d5f5430175547b6d972e300892258bfa6e1b0cf1c4058a73ad9f2'
RAW_SHA256 = '3bbaf27ff0c10ff68d8a195a82f39eadee266f324067bd0a66081710be30b4ec'
RAW_BYTES = 707448
CACHE = '/root/.cache/solana/v1.37/platform-tools'
MANIFEST = '/build/programs/token-metadata/Cargo.toml'
HOST_TOOLCHAIN = '1.69.0-x86_64-unknown-linux-gnu'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def inputs(repo=REPO):
    root = repo / 'repro/pump/metaplex-candidate-build-11'
    result = {name: (root / name).read_bytes() for name in PINS}
    for name, raw in result.items():
        require(sha(raw) == PINS[name], 'Changed historical input: ' + name)
    return result


def source_members(archive_path, expected):
    require(file_sha(archive_path) == SOURCE_SHA256, 'Source archive identity differs')
    prefix = 'mpl-token-metadata-' + SOURCE_COMMIT + '/'
    result = {}
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive:
            if member.isdir():
                continue
            require(member.isfile() and member.name.startswith(prefix), 'Unexpected source archive member')
            name = member.name[len(prefix):]
            path = PurePosixPath(name)
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                    and name not in result and name in expected, 'Unexpected source archive path')
            raw = archive.extractfile(member).read()
            require(sha(raw) == expected[name], 'Source file differs: ' + name)
            result[name] = raw
    require(set(result) == set(expected), 'Source file inventory differs')
    return result


def check_source(source, expected):
    actual = {name: file_sha(source / name) for name in expected}
    require(actual == expected, 'Build source or lockfile changed')
    return actual


def registry_archives(registry, lock):
    expected = {(p['name'], p['version']): p['checksum'] for p in lock['package']
                if p.get('source', '').startswith('registry+')}
    actual = {}
    for path in sorted(registry.glob('cache/*/*.crate')):
        key, = [key for key in expected if path.name == f'{key[0]}-{key[1]}.crate']
        require(key not in actual, 'Duplicate registry archive')
        digest = file_sha(path)
        require(digest == expected[key], 'Registry archive checksum differs: ' + path.name)
        actual[key] = {'name': key[0], 'version': key[1], 'path': path.relative_to(registry).as_posix(),
                       'bytes': path.stat().st_size, 'sha256': digest}
    require(set(actual) == set(expected), 'Registry archive set differs from lockfile')
    return list(actual.values())


def raw_result(path):
    size, digest = path.stat().st_size, file_sha(path)
    return {'bytes': size, 'sha256': digest, 'expected_bytes': RAW_BYTES,
            'expected_sha256': RAW_SHA256, 'raw_candidate11_equal': size == RAW_BYTES and digest == RAW_SHA256,
            'padding_bytes_added': 0, 'binary_rewritten': False, 'deployed_identity_claimed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(sys.platform == 'linux' and platform.machine() == 'x86_64', 'Use an isolated Linux x86_64 runner')
    out = args.output.resolve()
    require(not out.exists(), 'Fresh output directory required')
    source, downloads, evidence = out / 'source', out / 'downloads', out / 'evidence'
    trace_directory = out / 'trace'
    for path in (source, downloads, evidence, out / 'registry', out / 'git-cache', trace_directory):
        path.mkdir(parents=True)
    pinned = inputs()
    for name, raw in pinned.items():
        (evidence / name).write_bytes(raw)
    (evidence / 'trace.py').write_bytes(Path(__file__).read_bytes())
    wrapper = evidence / 'rustc-trace-wrapper.sh'
    wrapper.write_bytes((PACKAGE / 'rustc-trace-wrapper.sh').read_bytes())
    wrapper.chmod(0o755)
    baseline = json.loads(pinned['upstream-source-manifest.json'])
    patched = json.loads(pinned['source-manifest.json'])
    state = {'status': 'STARTED', 'observed_at': datetime.now(timezone.utc).isoformat(), 'commands': [],
             'image': IMAGE, 'source_commit': SOURCE_COMMIT, 'program_replays': 0,
             'captured_executable_mounted': False, 'build_network': 'none', 'diagnostic_only': True}
    container = None
    container_name = 'startrack3r-metaplex-build-' + uuid.uuid4().hex[:12]
    start_attempted = False

    def record():
        save(evidence / 'observation.json', state)

    def run(label, command, cwd=None, timeout=300, required=True):
        try:
            result = subprocess.run(command, cwd=cwd, capture_output=True, timeout=timeout)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code, stdout, stderr = None, error.stdout or b'', error.stderr or b''
        row = {'label': label, 'command': command, 'cwd': str(cwd) if cwd else None, 'returncode': code}
        for channel, raw in [('stdout', stdout), ('stderr', stderr)]:
            filename = label + '.' + channel + '.log'
            (evidence / filename).write_bytes(raw)
            row[channel] = {'file': filename, 'bytes': len(raw), 'sha256': sha(raw)}
        state['commands'].append(row)
        record()
        print(json.dumps({'command': label, 'returncode': code}), flush=True)
        if required:
            require(code == 0, label + ' failed; output retained')
        return stdout.decode('utf-8'), stderr.decode('utf-8'), code

    def download(label, url, path):
        run(label, ['curl', '--fail', '--location', '--retry', '2', '--retry-all-errors',
                    '--connect-timeout', '30', '--max-time', '300', '--output', str(path), url], timeout=1000)

    try:
        source_archive = downloads / 'upstream-source.tar.gz'
        download('download-source', SOURCE_URL, source_archive)
        members = source_members(source_archive, baseline)
        for name, raw in members.items():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        git_apply = ['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf', 'apply']
        run('check-patch', git_apply + ['--check', str(evidence / 'source.patch')], cwd=source)
        run('apply-patch', git_apply + [str(evidence / 'source.patch')], cwd=source)
        save(evidence / 'actual-source-before.json.gz', check_source(source, patched))
        lock = tomllib.loads((source / 'programs/token-metadata/Cargo.lock').read_text())
        tools_archive = downloads / 'platform-tools.tar.bz2'
        download('download-tools', TOOLS_URL, tools_archive)
        require(tools_archive.stat().st_size == TOOLS_BYTES and file_sha(tools_archive) == TOOLS_SHA256,
                'Platform tools archive identity differs')
        save(evidence / 'acquisition.json', {'source_url': SOURCE_URL, 'source_archive_sha256': SOURCE_SHA256,
            'source_archive_bytes': source_archive.stat().st_size, 'tools_url': TOOLS_URL,
            'tools_archive_sha256': TOOLS_SHA256, 'tools_archive_bytes': TOOLS_BYTES})
        run('pull-image', ['docker', 'pull', '--platform', 'linux/amd64', IMAGE], timeout=600)
        stdout, _, _ = run('inspect-image', ['docker', 'image', 'inspect', IMAGE])
        image, = json.loads(stdout)
        require(image['Id'] == IMAGE_ID and IMAGE in image['RepoDigests'], 'Pinned image differs')
        # With all capabilities dropped, container root cannot override host UID
        # permissions. Change ownership only of this fresh experiment's public
        # source/cache mounts; no checkout, home directory or credentials are mounted.
        run('prepare-container-ownership', ['sudo', '--non-interactive', 'chown', '-R', '0:0',
            str(source), str(out / 'registry'), str(out / 'git-cache'), str(trace_directory)])
        mounts = ['--mount', f'type=bind,source={source},target=/build',
                  '--mount', f'type=bind,source={out / "registry"},target=/usr/local/cargo/registry',
                  '--mount', f'type=bind,source={out / "git-cache"},target=/usr/local/cargo/git']
        base = ['docker', 'run', '--rm', '--platform', 'linux/amd64', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges']
        # cargo fetch acquires dependencies without compiling build scripts or programs.
        run('fetch-locked-dependencies', base + mounts + ['--network', 'bridge',
            '-e', 'CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse', '-e', 'RUSTUP_TOOLCHAIN=' + HOST_TOOLCHAIN,
            IMAGE, 'cargo', 'fetch', '--locked', '--manifest-path', MANIFEST], timeout=900)
        check_source(source, patched)
        save(evidence / 'registry-archives.json.gz', registry_archives(out / 'registry', lock))
        rooster_manifest, = list((out / 'git-cache/checkouts').glob('rooster-*/*/program/Cargo.toml'))
        rooster = rooster_manifest.parents[1]
        git_sources = [p for p in lock['package'] if p.get('source', '').startswith('git+')]
        require(len(git_sources) == 1 and git_sources[0]['name'] == 'rooster', 'Unexpected Git dependency')
        git_dependency = ['git', '-c', 'safe.directory=' + str(rooster), '-C', str(rooster)]
        stdout, _, _ = run('git-dependency-revision', git_dependency + ['rev-parse', 'HEAD'])
        require(stdout.strip() == git_sources[0]['source'].split('#')[1], 'Git dependency revision differs')
        run('git-dependency-clean', git_dependency + ['diff', '--exit-code', 'HEAD'])
        start_attempted = True
        stdout, _, _ = run('start-offline-build-container', base + mounts + [
            '--detach', '--name', container_name, '--network', 'none',
            '--tmpfs', '/root/.cache:rw,exec,nosuid,nodev,size=2g',
            '--mount', f'type=bind,source={tools_archive},target=/input/platform-tools.tar.bz2,readonly',
            '--mount', f'type=bind,source={wrapper},target=/observer/rustc-trace-wrapper.sh,readonly',
            '--mount', f'type=bind,source={trace_directory},target=/trace',
            '-e', 'CARGO_NET_OFFLINE=true', '-e', 'CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse',
            IMAGE, 'sleep', '3600'])
        container = stdout.strip()
        require(re.fullmatch('[0-9a-f]{64}', container), 'Invalid container ID')
        prefix = ['docker', 'exec', container]
        run('create-tools-cache', prefix + ['mkdir', '-p', CACHE])
        run('install-tools', prefix + ['tar', '--no-same-owner', '--no-same-permissions',
            '-xjf', '/input/platform-tools.tar.bz2', '-C', CACHE], timeout=300)
        driver = CACHE + '/rust/lib/librustc_driver-f767167903553d17.so'
        stdout, _, _ = run('driver-before', prefix + ['sha256sum', driver])
        require(stdout.split()[0] == DRIVER_SHA256, 'Compiler driver differs')
        run('compiler-version', prefix + [CACHE + '/rust/bin/rustc', '--version', '--verbose'])
        help_stdout, help_stderr, _ = run('compiler-trace-options', prefix + [CACHE + '/rust/bin/rustc',
            '--print', 'target-cpus', '--target', 'sbf-solana-solana', '-Cllvm-args=--help-hidden'])
        require(all(re.search(r'--' + option + r'(?:=|\s)', help_stdout + help_stderr)
                    for option in ('print-before', 'print-after')), 'Actual compiler did not report trace options')
        _, trace_stderr, _ = run('build-candidate11-traced', ['docker', 'exec', '-e', 'RUSTUP_TOOLCHAIN=' + HOST_TOOLCHAIN,
            '-e', 'RUSTC_WRAPPER=/observer/rustc-trace-wrapper.sh',
            '-w', '/build/programs/token-metadata', container, 'cargo', 'build-sbf', '--offline', '--',
            '--config', 'registries.crates-io.protocol="sparse"', '--locked', '--offline',
            '--manifest-path', MANIFEST], timeout=1500)
        stdout, _, _ = run('driver-after', prefix + ['sha256sum', driver])
        require(stdout.split()[0] == DRIVER_SHA256, 'Compiler driver changed')
        save(evidence / 'actual-source-after.json.gz', check_source(source, patched))
        raw = source / 'programs/token-metadata/target/deploy/token_metadata.so'
        (evidence / 'token_metadata.so').write_bytes(raw.read_bytes())
        result = raw_result(raw)
        save(evidence / 'raw-result.json', result)
        state.update(status='RAW_MATCH' if result['raw_candidate11_equal'] else 'RAW_MISMATCH', raw=result)
        require(result['raw_candidate11_equal'], 'Raw candidate11 gate differs; actual bytes retained')
        invocations = list(trace_directory.glob('rustc-*.argv'))
        require(len(invocations) == 1, 'Expected one actual token_metadata codegen invocation')
        require('process_utilize' in trace_stderr and 'Finalize ISel' in trace_stderr
                and 'Branch Probability Basic Block Placement' in trace_stderr,
                'Raw match, but requested compiler snapshots are incomplete')
        state['trace_snapshots_present'] = True
    except Exception as error:
        if state['status'] != 'RAW_MISMATCH':
            state['status'] = 'FAILED'
        state.update(error_type=type(error).__name__, error=str(error))
        raise
    finally:
        try:
            for path in sorted(trace_directory.glob('rustc-*.argv')):
                (evidence / path.name).write_bytes(path.read_bytes())
            if start_attempted:
                target = container if container and re.fullmatch('[0-9a-f]{64}', container) else container_name
                _, _, code = run('stop-build-container', ['docker', 'stop', '--time', '1', target], required=False)
                state['cleanup_succeeded'] = code == 0
                if code != 0 and state['status'] == 'RAW_MATCH':
                    state['status'] = 'CLEANUP_FAILED'
        finally:
            record()
    require(state['status'] == 'RAW_MATCH', 'Observation incomplete')


if __name__ == '__main__':
    main()
