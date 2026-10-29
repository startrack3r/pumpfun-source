"""Corruption controls for the recorded compiler boundary, without target execution."""
from pathlib import Path
import gzip
import importlib.util
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('analyze', HERE / 'analyze.py')
analyze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analyze)


class RecordedBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((HERE / 'runs/05-all-pass-trace/stderr.log.gz').read_bytes())
        cls.report = analyze.analyze(cls.raw)

    def test_recorded_trace_includes_indexed_blocks(self):
        rows = self.report['snapshots']
        self.assertEqual(self.report['machine_snapshot_count'], 116)
        self.assertGreater(rows[285]['block_count'], 0)
        self.assertGreater(rows[317]['block_count'], 0)

    def mutate(self, row, old, new):
        start, end = row['offset'], row['end']
        body = self.raw[start:end]
        self.assertIn(old, body)
        return self.raw[:start] + body.replace(old, new, 1) + self.raw[end:]

    def test_first_machine_polarity_corruption_rejected(self):
        raw = self.mutate(self.report['first_machine'],
                          b'JNE_rr %18:gpr, killed %191:gpr', b'JEQ_rr %18:gpr, killed %191:gpr')
        with self.assertRaisesRegex(ValueError, 'borrow predicate'):
            analyze.analyze(raw)

    def test_ir_polarity_corruption_rejected(self):
        raw = self.mutate(self.report['last_ir'], b'%227 = icmp eq', b'%227 = icmp ne')
        with self.assertRaisesRegex(ValueError, 'IR equality|IR success-adjacency boundary'):
            analyze.analyze(raw)

    def test_successor_identity_corruption_rejected(self):
        raw = self.mutate(self.report['first_machine'], b'bb.26 (%ir-block.236)', b'bb.26 (%ir-block.999)')
        with self.assertRaisesRegex(ValueError, 'successor IR identities'):
            analyze.analyze(raw)

    def test_truncated_capture_rejected(self):
        with self.assertRaises(ValueError):
            analyze.analyze(self.raw[:self.report['snapshots'][-1]['offset']])

    def test_earlier_adjacency_claim_rejected(self):
        before = self.report['ir_adjacency_boundary']['before']
        raw = self.mutate(before, before['following_block'].encode(), b'')
        with self.assertRaisesRegex(ValueError, 'IR success-adjacency boundary'):
            analyze.analyze(raw)


if __name__ == '__main__':
    unittest.main()
