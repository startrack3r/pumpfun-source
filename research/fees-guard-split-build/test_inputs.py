import json
from pathlib import Path
import tempfile
import unittest
import run as r


class InputTests(unittest.TestCase):
    def test_exact_source_set_and_single_guard_delta(self):
        files = r.source_members()
        self.assertEqual(len(files), 26)
        before = files[r.SOURCE_FILE]
        after = r.split_guard(before)
        self.assertEqual(after.replace(r.NEW, r.OLD, 1), before)
        self.assertNotEqual(after, before)

    def test_second_patch_application_rejected(self):
        raw = r.source_members()[r.SOURCE_FILE]
        with self.assertRaisesRegex(ValueError, 'changed or already split'):
            r.split_guard(r.split_guard(raw))

    def test_changed_guard_rejected(self):
        raw = r.source_members()[r.SOURCE_FILE].replace(r.OLD, r.OLD.replace(b' < 8', b' < 9'), 1)
        with self.assertRaisesRegex(ValueError, 'changed or already split'):
            r.split_guard(raw)

    def test_raw_gate_rejects_padding_and_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'output'
            path.write_bytes(b'RAW'); policy = {'baseline': r.raw_record(path)}
            self.assertEqual(r.require_baseline(path, policy), policy['baseline'])
            for raw in (b'RAW\0', b'RAw'):
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'Fresh baseline differs'):
                    r.require_baseline(path, policy)

    def test_only_phase_environment_changes(self):
        a, b = r.environment('baseline'), r.environment('split')
        self.assertEqual({k for k in a if a[k] != b[k]}, {'FEES_PROBE_PHASE'})
        self.assertEqual(a['CARGO_NET_OFFLINE'], 'true')
        self.assertEqual(a['CARGO_TARGET_SBF_SOLANA_SOLANA_RUSTFLAGS'], '-Zremap-cwd-prefix=')


if __name__ == '__main__':
    unittest.main()
