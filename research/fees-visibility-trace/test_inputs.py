import importlib.util
from pathlib import Path
import unittest
import run

spec = importlib.util.spec_from_file_location('wrapper', Path(__file__).with_name('rustc-wrapper.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class Inputs(unittest.TestCase):
    def test_exact_source_delta(self):
        a, b = run.source_members('control'), run.source_members('origins')
        name = 'programs/pump-fees/src/lib.rs'
        self.assertEqual(len(a), 42)
        self.assertEqual([n for n in a if a[n] != b[n]], [name])
        self.assertEqual(a[name].replace(b'\nmod instructions;', b'\npub mod instructions;'), b[name])

    def test_no_target_inputs(self):
        self.assertFalse(any(n.endswith(('.so', '.o', '.rlib', '.bc', '.ll')) for n in run.source_members()))

    def test_dependency_passthrough(self):
        args = ['rustc', '--crate-name', 'anchor_lang', '--target', 'sbpf-solana-solana']
        self.assertEqual(w.instrument(args), args)
        self.assertEqual(w.instrument(['rustc', '-vV']), ['rustc', '-vV'])

    def test_root_diagnostics_only(self):
        args = ['rustc', '--crate-name', 'pump_fees_candidate', '--emit=dep-info,link']
        self.assertEqual(w.instrument(args), args + w.FLAGS)
        self.assertEqual(w.FLAGS[:2], ['-Cllvm-args=-print-before-all', '-Cllvm-args=-print-after-all'])
        self.assertTrue(w.FLAGS[2].startswith('-Cllvm-args=-filter-print-funcs='))

    def test_offline_build_environments(self):
        for phase in ('control', 'origins'):
            self.assertEqual(run.environment(phase)['CARGO_NET_OFFLINE'], 'true')

    def test_four_distinct_raw_output_gates(self):
        policy = run.read(run.P / 'policy.json')
        rows = [row for variants in policy['expected'].values() for row in variants.values()]
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({r['sha256'] for r in rows}), 4)
        self.assertTrue(all(r['bytes'] > 800000 for r in rows))


if __name__ == '__main__':
    unittest.main()
