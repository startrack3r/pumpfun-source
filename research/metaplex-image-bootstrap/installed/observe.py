"""Observe an authenticated v1.37 compiler in a network-disabled pinned container.

No program source or captured executable is supplied, and no program is compiled.
The ephemeral compiler installation is new evidence, not historical attribution.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import posixpath
import re
import subprocess
import sys
import tarfile
import uuid

IMAGE = 'solanafoundation/solana-verifiable-build@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467'
IMAGE_ID = 'sha256:8a1c7e411dda3083f89fc82e9fbcbc57cfffed615853f11c124ef3df1443978f'
ARCHIVE_URL = 'https://github.com/anza-xyz/platform-tools/releases/download/v1.37/platform-tools-linux-x86_64.tar.bz2'
ARCHIVE_SHA256 = '8d5153589dbe19635affe937663cf4555a7e69a62d91ab4a1df064aaa8d5f066'
ARCHIVE_BYTES = 362756282
CACHE = '/root/.cache/solana/v1.37/platform-tools'
RUSTC = CACHE + '/rust/bin/rustc'
DRIVER = 'rust/lib/librustc_driver-f767167903553d17.so'
MEMBERS = {
    'rust/bin/rustc': (17264, '7194df9c12e893cfa88fff5dd821d02d45910b4d375e13677b4723f45769a384'),
    DRIVER: (197537432, 'e7d221509c0d5f5430175547b6d972e300892258bfa6e1b0cf1c4058a73ad9f2'),
    'version.md': (249, '34887eda294cf872fa8ca0f444ea95308ce8b5b1b8db24de4b32ef298e889b38'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def check_member(member):
    name = PurePosixPath(member.name)
    require(not name.is_absolute() and '..' not in name.parts and '\\' not in member.name,
            'Unsafe archive member name')
    require(member.isfile() or member.isdir() or member.issym() or member.islnk(),
            'Unexpected archive member type')
    if member.issym() or member.islnk():
        target = member.linkname
        destination = posixpath.normpath(posixpath.join(posixpath.dirname(name.as_posix()), target)
                                        if member.issym() else target)
        require(not posixpath.isabs(target) and destination != '..' and not destination.startswith('../'),
                'Archive link escapes installation')
    return name.as_posix()


def audit_archive(path):
    digest, count = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while raw := stream.read(1024 * 1024):
            digest.update(raw)
            count += len(raw)
    require(count == ARCHIVE_BYTES and digest.hexdigest() == ARCHIVE_SHA256,
            f'Wrong compiler archive: actual bytes={count}, sha256={digest.hexdigest()}')
    inventory, selected, seen = [], {}, set()
    with tarfile.open(path, 'r|bz2') as archive:
        for member in archive:
            name = check_member(member)
            require(name not in seen, 'Duplicate archive member')
            seen.add(name)
            inventory.append({'name': name, 'type': member.type.decode('ascii'), 'bytes': member.size,
                              'mode': member.mode, 'linkname': member.linkname})
            if name in MEMBERS:
                require(member.isfile(), 'Selected compiler member is not a regular file')
                digest, data = hashlib.sha256(), bytearray()
                file = archive.extractfile(member)
                while raw := file.read(1024 * 1024):
                    digest.update(raw)
                    if member.size < 1024:
                        data.extend(raw)
                require((member.size, digest.hexdigest()) == MEMBERS[name], 'Compiler member identity differs')
                selected[name] = {'bytes': member.size, 'sha256': digest.hexdigest()}
                if data:
                    selected[name]['text'] = data.decode('utf-8')
    require(set(selected) == set(MEMBERS), 'Missing compiler member')
    return inventory, selected


def loaded_initializers(stderr):
    paths = sorted(set(re.findall(r'calling init:\s+(/[^\s]+)', stderr)))
    require(paths and any('librustc_driver-' in path for path in paths), 'No loaded rustc driver in loader trace')
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(sys.platform == 'linux' and platform.machine() == 'x86_64', 'Use an isolated Linux x86_64 runner')
    output = args.output.resolve()
    require(not output.exists(), 'Fresh output directory required')
    evidence, downloads = output / 'evidence', output / 'downloads'
    evidence.mkdir(parents=True)
    downloads.mkdir()
    (evidence / 'observe.py').write_bytes(Path(__file__).read_bytes())
    state = {'status': 'STARTED', 'observed_at': datetime.now(timezone.utc).isoformat(),
             'image': IMAGE, 'commands': [], 'container_network': 'none', 'source_mounted': False,
             'captured_executable_mounted': False, 'program_builds': 0, 'program_replays': 0,
             'historical_loaded_library_identity_proven': False, 'actual_historical_target_cpu': None}
    container_name = 'startrack3r-metaplex-observe-' + uuid.uuid4().hex[:12]
    container = None
    container_start_attempted = False

    def save():
        save_json(evidence / 'observation.json', state)

    def run(label, command, required=True, timeout=180):
        try:
            result = subprocess.run(command, capture_output=True, timeout=timeout)
            returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            returncode, stdout, stderr = None, error.stdout or b'', error.stderr or b''
        row = {'label': label, 'command': command, 'returncode': returncode}
        for name, raw in (('stdout', stdout), ('stderr', stderr)):
            filename = label + '.' + name + '.log'
            (evidence / filename).write_bytes(raw)
            row[name] = {'file': filename, 'bytes': len(raw), 'sha256': sha(raw)}
        state['commands'].append(row)
        save()
        if required:
            require(returncode == 0, label + ' failed; actual output retained')
        return stdout.decode('utf-8'), stderr.decode('utf-8'), returncode

    try:
        archive_path = downloads / 'platform-tools-linux-x86_64.tar.bz2'
        # Preserve transfer diagnostics, including transient failures, before auditing bytes.
        run('download-archive', ['curl', '--fail', '--location', '--retry', '2',
            '--retry-all-errors', '--connect-timeout', '30', '--max-time', '300',
            '--output', str(archive_path), ARCHIVE_URL], timeout=1000)
        inventory, selected = audit_archive(archive_path)
        (evidence / 'archive-inventory.json.gz').write_bytes(gzip.compress(
            (json.dumps(inventory, separators=(',', ':')) + '\n').encode(), mtime=0))
        save_json(evidence / 'archive.json', {'url': ARCHIVE_URL, 'sha256': ARCHIVE_SHA256,
            'bytes': ARCHIVE_BYTES, 'publisher_digest': None, 'members': len(inventory), 'selected': selected})
        run('pull-image', ['docker', 'pull', '--platform', 'linux/amd64', IMAGE], timeout=600)
        raw, _, _ = run('inspect-image', ['docker', 'image', 'inspect', IMAGE])
        inspected = json.loads(raw)
        require(len(inspected) == 1 and inspected[0]['Id'] == IMAGE_ID and IMAGE in inspected[0]['RepoDigests'],
                'Wrong pinned image')
        container_start_attempted = True
        raw, _, _ = run('start-container', ['docker', 'run', '--rm', '--detach', '--name', container_name,
            '--platform', 'linux/amd64', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,nodev,size=16m',
            '--tmpfs', '/root/.cache:rw,exec,nosuid,nodev,size=2g',
            '--mount', 'type=bind,source=' + str(archive_path) + ',target=/input/platform-tools.tar.bz2,readonly',
            '--entrypoint', 'sleep', IMAGE, '1800'])
        container = raw.strip()
        require(re.fullmatch('[0-9a-f]{64}', container), 'Unexpected container ID')
        run('cold-compiler-absent', ['docker', 'exec', container, 'test', '!', '-e', RUSTC])
        run('create-cache', ['docker', 'exec', container, 'mkdir', '-p', CACHE])
        run('install-authenticated-archive', ['docker', 'exec', container, 'tar', '--no-same-owner',
            '--no-same-permissions', '-xjf', '/input/platform-tools.tar.bz2', '-C', CACHE], timeout=300)
        for index, (name, (_, expected)) in enumerate(MEMBERS.items()):
            stdout, _, _ = run(f'installed-member-{index:02d}', ['docker', 'exec', container, 'sha256sum', CACHE + '/' + name])
            require(stdout.split()[0] == expected, 'Installed compiler member differs')
        stdout, stderr, _ = run('rustc-loaded-version', ['docker', 'exec', '-e', 'LD_DEBUG=libs', container,
                                                     RUSTC, '--version', '--verbose'])
        state['rustc_version'] = stdout
        state['loaded_library_initializers'] = loaded_initializers(stderr)
        loaded = []
        for index, path in enumerate(state['loaded_library_initializers']):
            resolved, _, _ = run(f'loaded-library-{index:02d}-path', ['docker', 'exec', container, 'readlink', '-f', path])
            digest, _, _ = run(f'loaded-library-{index:02d}-sha256', ['docker', 'exec', container, 'sha256sum', resolved.strip()])
            loaded.append({'reported_path': path, 'resolved_path': resolved.strip(), 'sha256': digest.split()[0]})
        require(any(row['resolved_path'] == CACHE + '/' + DRIVER and row['sha256'] == MEMBERS[DRIVER][1]
                    for row in loaded), 'Fresh loaded driver does not match authenticated archive')
        save_json(evidence / 'loaded-libraries.json', loaded)
        run('rustc-ldd', ['docker', 'exec', container, 'ldd', RUSTC])
        targets, _, _ = run('rustc-targets', ['docker', 'exec', container, RUSTC, '--print', 'target-list'])
        state['available_bpf_sbf_targets'] = [target for target in targets.splitlines() if 'bpf' in target or 'sbf' in target]
        require(state['available_bpf_sbf_targets'], 'No BPF/SBF targets reported')
        for index, target in enumerate(state['available_bpf_sbf_targets']):
            for label, arguments in [('spec', ['-Z', 'unstable-options', '--print', 'target-spec-json']),
                                      ('cpus', ['--print', 'target-cpus']), ('features', ['--print', 'target-features'])]:
                run(f'target-{index:02d}-{label}', ['docker', 'exec', container, RUSTC, *arguments, '--target', target], required=False)
        state.update(status='OBSERVED', fresh_loaded_driver_matches_archive=True,
            limits='New authenticated installation and compiler capability observations only. No historical loaded-library attribution, actual historical CPU inference, program compilation or raw target-byte improvement.')
    except Exception as error:
        state.update(status='FAILED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        cleanup_failed = False
        try:
            if container_start_attempted:
                target = container if container and re.fullmatch('[0-9a-f]{64}', container) else container_name
                _, _, status = run('stop-container', ['docker', 'stop', '--time', '1', target], required=False)
                if status != 0:
                    cleanup_failed = True
                    state['cleanup_failed'] = True
                    if state['status'] != 'FAILED':
                        state['status'] = 'CLEANUP_FAILED'
        finally:
            save()
        if cleanup_failed and state['status'] == 'CLEANUP_FAILED':
            raise RuntimeError('Observation retained, but container cleanup failed')
    print(json.dumps({'status': state['status'], 'commands': len(state['commands']),
                      'targets': state.get('available_bpf_sbf_targets')}, indent=2))


if __name__ == '__main__':
    main()
