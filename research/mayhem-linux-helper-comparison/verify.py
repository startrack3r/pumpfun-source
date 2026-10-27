#!/usr/bin/env python3
"""Offline saved-artifact and helper comparison; no downloads or target execution."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare

HERE = Path(__file__).resolve().parent


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def checked(data, row, label):
    if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
        raise ValueError("identity differs: " + label)


def check_inputs(package, repo):
    for row in read(package / "inputs.json")["files"]:
        name = row["path"]
        parts = Path(name).parts
        if Path(name).is_absolute() or ".." in parts or "\\" in name or ":" in name:
            raise ValueError("invalid input path")
        raw = (repo / name).read_bytes()
        checked(raw, row, name)
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != row["git_blob"]:
            raise ValueError("Git blob differs: " + name)


def verify(package=HERE, repo=None):
    repo = HERE.parents[1] if repo is None else repo
    for row in read(package / "manifest.json"):
        checked((package / row["path"]).read_bytes(), row, row["path"])
    check_inputs(package, repo)
    comparison, findings = compare.analyze(repo)
    # Serialize tuples to their JSON array representation.
    comparison = json.loads(json.dumps(comparison))
    findings = json.loads(json.dumps(findings))
    if comparison != read(package / "comparison.json.gz"):
        raise ValueError("comparison differs")
    if findings != read(package / "findings.json"):
        raise ValueError("findings differ")
    return {key: findings[key] for key in (
        "method_counts", "distinct_raw_capture_ranges", "recorded_source_inputs_equal",
        "linux_builds_executed_here", "target_executions", "scope")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    args = parser.parse_args()
    print(json.dumps(verify(repo=args.repo), indent=2))
