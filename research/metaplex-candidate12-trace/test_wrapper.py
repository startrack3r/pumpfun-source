"""Exercise argv preservation and program-only observations with a fake compiler."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

WRAPPER = Path(__file__).resolve().with_name('rustc-trace-wrapper.sh')
FLAGS = ['-Cllvm-args=-print-before=codegenprepare,finalize-isel', '-Cllvm-args=-print-after=codegenprepare,finalize-isel,branch-folder,block-placement,sbf-mi-pemit-peephole', '-Cllvm-args=-print-isel-input', '-Cllvm-args=-filter-print-funcs=_ZN14token_metadata9processor4uses7utilize15process_utilize17h9789c7990f4c0b83E', '-Cllvm-args=-debug-pass=Structure']


@unittest.skipUnless(sys.platform == 'linux', 'Wrapper executes on the isolated Linux runner')
class WrapperTests(unittest.TestCase):
    def invoke(self, arguments):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        compiler = root / 'fake compiler'
        compiler.write_text('#!/usr/bin/env python3\nimport json,os,sys\n'
                            'open(os.environ["MOCK_RESULT"],"w").write(json.dumps(sys.argv[1:]))\n')
        compiler.chmod(0o755)
        result = root / 'result.json'
        env = dict(os.environ, MOCK_RESULT=str(result), TRACE_OUTPUT_DIRECTORY=str(root))
        subprocess.run(['bash', str(WRAPPER), str(compiler), *arguments], env=env, check=True)
        return compiler, json.loads(result.read_text()), list(root.glob('rustc-*.argv'))

    def test_dependency_command_is_unchanged(self):
        arguments = ['--crate-name', 'dependency', '--emit=dep-info,link', '--cfg', 'value="has space"']
        _, actual, records = self.invoke(arguments)
        self.assertEqual(actual, arguments)
        self.assertEqual(records, [])

    def test_program_metadata_probe_is_unchanged(self):
        arguments = ['--crate-name', 'token_metadata', '--emit=metadata']
        _, actual, records = self.invoke(arguments)
        self.assertEqual(actual, arguments)
        self.assertEqual(records, [])

    def test_program_codegen_appends_only_trace_flags_and_records_exact_argv(self):
        arguments = ['--crate-name', 'token_metadata', '--emit=dep-info,metadata,link', '--cfg', 'value="has space"']
        compiler, actual, records = self.invoke(arguments)
        self.assertEqual(actual, arguments + FLAGS)
        record, = records
        self.assertEqual(record.read_bytes(), b'\0'.join(str(arg).encode() for arg in [compiler, *arguments, *FLAGS]) + b'\0')


if __name__ == '__main__':
    unittest.main()
