#!/usr/bin/python3
"""Observe only the root crate's selected LLVM function, then exec rustc."""
import json
import os
from pathlib import Path
import sys

FUNCTION = '_ZN11anchor_lang8accounts7account16Account$LT$T$GT$8try_from17h35c4169a6471ee49E'
FLAGS = ['-Cllvm-args=-print-before=stack-coloring,prologepilog',
         '-Cllvm-args=-print-after=stack-coloring,prologepilog',
         '-Cllvm-args=-filter-print-funcs=' + FUNCTION]


def instrument(args):
    root = '--crate-name' in args and args[args.index('--crate-name')+1] == 'pump_fees_candidate'
    return args + FLAGS if root else list(args)


if __name__ == '__main__':
    before = sys.argv[1:]; actual = instrument(before)
    if actual != before:
        assert os.environ['FEES_PROBE_PHASE'] == 'trace'
        dest = Path('/gate/evidence/trace-rustc-argv.json')
        assert not dest.exists(), 'Duplicate root compiler invocation'
        dest.write_text(json.dumps({'input':before,'actual':actual,'added':FLAGS},indent=2)+'\n')
    os.execv(actual[0],actual)
