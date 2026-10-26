import importlib.util
import unittest
from pathlib import Path
import run

spec=importlib.util.spec_from_file_location('wrapper',Path(__file__).with_name('rustc-wrapper.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


class InputTests(unittest.TestCase):
    def test_exact_body_direct_source(self):
        files=run.source_members()
        self.assertEqual(len(files),26)
        self.assertFalse(any(p.endswith(('.so','.o','.rlib')) for p in files))
        raw=files['programs/pump-fees/src/types.rs']
        self.assertIn(b'Self::try_deserialize_unchecked(&mut &buf[8..])',raw)
        self.assertIn(b'if buf.len() < 2504',raw)

    def test_dependency_invocation_unchanged(self):
        args=['rustc','--crate-name','anchor_lang','--target','sbf-solana-solana']
        self.assertEqual(w.instrument(args),args)
        self.assertEqual(w.instrument(['rustc','-vV']),['rustc','-vV'])

    def test_root_changes_only_diagnostic_arguments(self):
        args=['rustc','--crate-name','pump_fees_candidate','--emit=dep-info,link']
        self.assertEqual(w.instrument(args),args+w.FLAGS)
        self.assertEqual(len(w.FLAGS),3)
        self.assertTrue(all(x.startswith(('-Cllvm-args=-print-before=', '-Cllvm-args=-print-after=',
                                          '-Cllvm-args=-filter-print-funcs=')) for x in w.FLAGS))
        self.assertEqual(args,['rustc','--crate-name','pump_fees_candidate','--emit=dep-info,link'])

    def test_compile_is_offline(self):
        self.assertEqual(run.environment('trace')['CARGO_NET_OFFLINE'],'true')


if __name__=='__main__':unittest.main()
