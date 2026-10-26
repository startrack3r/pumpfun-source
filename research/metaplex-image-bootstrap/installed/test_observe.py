"""Small source-independent archive and loader-trace tests; no compiler execution."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import observe


class ObservationTests(unittest.TestCase):
    def test_archive_names_and_types_reject_escape(self):
        for name in ('../escape', '/absolute', 'windows\\separator'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Unsafe archive'):
                observe.check_member(tarfile.TarInfo(name))
        member = tarfile.TarInfo('pipe')
        member.type = tarfile.FIFOTYPE
        with self.assertRaisesRegex(ValueError, 'Unexpected archive member type'):
            observe.check_member(member)

    def test_link_resolution_stays_inside_installation(self):
        member = tarfile.TarInfo('./rust/bin/link')
        member.type = tarfile.SYMTYPE
        member.linkname = '../lib/driver.so'
        self.assertEqual(observe.check_member(member), 'rust/bin/link')
        for target in ('/etc/passwd', '../../../outside'):
            member.linkname = target
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'link escapes'):
                observe.check_member(member)
        member.type = tarfile.LNKTYPE
        member.linkname = '../outside'
        with self.assertRaisesRegex(ValueError, 'link escapes'):
            observe.check_member(member)

    def test_loader_search_attempt_is_not_loaded_driver_evidence(self):
        text = '12: trying file=/cache/librustc_driver-example.so\n12: calling init: /lib/libc.so.6\n'
        with self.assertRaisesRegex(ValueError, 'No loaded rustc driver'):
            observe.loaded_initializers(text)

    def test_loader_initializers_are_deduplicated(self):
        text = ('12: calling init: /cache/librustc_driver-example.so\n'
                '12: calling init: /lib/libc.so.6\n'
                '12: calling init: /lib/libc.so.6\n')
        self.assertEqual(observe.loaded_initializers(text),
                         ['/cache/librustc_driver-example.so', '/lib/libc.so.6'])

    def test_bad_archive_is_rejected_with_actual_identity_before_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'bad.tar.bz2'
            path.write_bytes(b'failed download')
            with self.assertRaisesRegex(ValueError, 'actual bytes=15, sha256='):
                observe.audit_archive(path)

    def test_synthetic_archive_complete_member_binding(self):
        contents = {name: ('synthetic ' + name).encode() for name in observe.MEMBERS}
        # Version metadata must be valid UTF-8; the synthetic binaries are never run.
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w:bz2') as archive:
            for name, raw in contents.items():
                member = tarfile.TarInfo('./' + name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
        raw = data.getvalue()
        expected = {name: (len(value), observe.sha(value)) for name, value in contents.items()}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'synthetic.tar.bz2'
            path.write_bytes(raw)
            with patch.object(observe, 'ARCHIVE_BYTES', len(raw)), \
                    patch.object(observe, 'ARCHIVE_SHA256', observe.sha(raw)), \
                    patch.dict(observe.MEMBERS, expected, clear=True):
                inventory, selected = observe.audit_archive(path)
            self.assertEqual(len(inventory), 3)
            self.assertEqual(set(selected), set(expected))


if __name__ == '__main__':
    unittest.main()
