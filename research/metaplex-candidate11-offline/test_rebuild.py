import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import rebuild


class Gates(unittest.TestCase):
    def test_pinned_historical_inputs(self):
        data = rebuild.inputs()
        self.assertEqual(len(json.loads(data['upstream-source-manifest.json'])), 812)
        self.assertEqual(len(json.loads(data['source-manifest.json'])), 812)

    def test_raw_gate_counts_trailing_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'raw.so'
            path.write_bytes(b'ELF')
            with patch.object(rebuild, 'RAW_BYTES', 3), patch.object(rebuild, 'RAW_SHA256', rebuild.sha(b'ELF')):
                self.assertTrue(rebuild.raw_result(path)['raw_candidate11_equal'])
                path.write_bytes(b'ELF\0')
                result = rebuild.raw_result(path)
                self.assertFalse(result['raw_candidate11_equal'])
                self.assertEqual(result['padding_bytes_added'], 0)
                self.assertEqual(path.read_bytes(), b'ELF\0')

    def test_registry_requires_all_locked_archives_and_checks_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / 'cache/index'
            cache.mkdir(parents=True)
            lock = {'package': [{'name': 'example', 'version': '1.0.0', 'source': 'registry+example',
                                  'checksum': rebuild.sha(b'archive')} ]}
            with self.assertRaisesRegex(ValueError, 'set differs'):
                rebuild.registry_archives(root, lock)
            archive = cache / 'example-1.0.0.crate'
            archive.write_bytes(b'archive')
            self.assertEqual(len(rebuild.registry_archives(root, lock)), 1)
            archive.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum differs'):
                rebuild.registry_archives(root, lock)

    def test_source_archive_inventory_and_content_are_both_bound(self):
        contents = {'Cargo.toml': b'manifest', 'src/lib.rs': b'source'}
        expected = {name: rebuild.sha(raw) for name, raw in contents.items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.tar.gz'
            with tarfile.open(path, 'w:gz') as archive:
                for name, raw in contents.items():
                    entry = tarfile.TarInfo('mpl-token-metadata-' + rebuild.SOURCE_COMMIT + '/' + name)
                    entry.size = len(raw)
                    archive.addfile(entry, io.BytesIO(raw))
            with patch.object(rebuild, 'SOURCE_SHA256', rebuild.file_sha(path)):
                self.assertEqual(rebuild.source_members(path, expected), contents)
                with self.assertRaisesRegex(ValueError, 'file inventory differs'):
                    rebuild.source_members(path, {**expected, 'missing': '0' * 64})
                with self.assertRaisesRegex(ValueError, 'file differs'):
                    rebuild.source_members(path, {**expected, 'src/lib.rs': '0' * 64})


if __name__ == '__main__':
    unittest.main()
