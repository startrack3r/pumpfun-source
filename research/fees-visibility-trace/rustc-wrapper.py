#!/usr/bin/python3
"""Add only filtered pass-printing arguments to the root crate invocation."""
import json
import os
from pathlib import Path
import sys

FUNCTION = '_ZN19pump_fees_candidate9__private8__global18initialize_buyback17h76c55443630219e4E'
FLAGS = ['-Cllvm-args=-print-before-all', '-Cllvm-args=-print-after-all',
         '-Cllvm-args=-filter-print-funcs=' + FUNCTION]


def instrument(args):
    root = '--crate-name' in args and args[args.index('--crate-name') + 1] == 'pump_fees_candidate'
    return args + FLAGS if root else list(args)


if __name__ == '__main__':
    before = sys.argv[1:]
    actual = instrument(before)
    if actual != before:
        phase = os.environ['FEES_PROBE_PHASE']
        assert phase in ('control', 'origins')
        destination = Path('/gate/evidence') / (phase + '-rustc-argv.json')
        assert not destination.exists(), 'Duplicate root invocation'
        destination.write_text(json.dumps(dict(input=before, actual=actual, added=FLAGS), indent=2) + '\n')
    os.execv(actual[0], actual)
