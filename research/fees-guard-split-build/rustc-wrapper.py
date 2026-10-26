#!/usr/bin/python3
"""Record the actual root invocation, then execute the unchanged compiler."""
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if '--crate-name' in args and args[args.index('--crate-name') + 1] == 'pump_fees_candidate':
    phase = os.environ['FEES_PROBE_PHASE']
    assert phase in ('baseline', 'split')
    path = Path('/gate/evidence') / (phase + '-rustc-argv.json')
    assert not path.exists(), 'Duplicate root compiler invocation'
    path.write_text(json.dumps(args, indent=2) + '\n')
os.execv(args[0], args)
