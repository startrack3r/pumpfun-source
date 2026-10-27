#!/usr/bin/env python3
"""Regression checks for retained host comparison and raw gain attribution."""
import argparse
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parent))
import compare as c
import verify as v

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


class HostComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result, cls.findings = c.analyze(REPO)
        cls.a = c.load_module(REPO / c.PARENT / "analyze.py", "test_boundaries")
        cls.capture = (REPO / c.ORIGINAL).read_bytes()
        cls.elf = cls.a.elf
        cls.ctx = c.pointer_entries(cls.elf.Elf(cls.capture), cls.a)

    @contextmanager
    def relocated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for row in v.read(HERE / "inputs.json")["files"]:
                dest = root / row["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / row["path"], dest)
            yield root

    def changed_relocation(self, address):
        raw = bytearray(self.capture)
        obj = self.elf.Elf(raw)
        count = 0
        for s in obj.sections:
            if s["type"] != 9:
                continue
            for at in range(s["offset"], s["offset"] + s["size"], 16):
                target, info = struct.unpack_from("<QQ", raw, at)
                if target == address:
                    self.assertEqual(info & 0xffffffff, 8)
                    struct.pack_into("<Q", raw, at + 8, 0)
                    count += 1
        self.assertEqual(count, 1)
        return self.elf.Elf(bytes(raw))

    def test_complete_packet(self):
        result = v.verify(HERE, REPO)
        self.assertEqual(result["method_counts"]["darwin"]["entry_bounded_raw_exact_matches"], 18)
        self.assertEqual(result["method_counts"]["linux"]["entry_bounded_raw_exact_matches"], 23)
        self.assertEqual(result["recorded_source_inputs_equal"], 14)

    def test_frozen_darwin_records_reproduce_exactly(self):
        old = json.loads((REPO / c.DARWIN / "helper-results.json").read_bytes())["builds"]["v154"]
        self.assertEqual(self.result["builds"]["darwin"], old)

    def test_five_raw_ranges_and_no_loss(self):
        rows = self.findings["distinct_raw_capture_ranges"]
        self.assertEqual(rows["gained"], [(599768, 40), (666624, 40),
                                          (697904, 80), (697984, 5128), (703896, 2008)])
        self.assertEqual(rows["lost"], [])

    def test_type_id_pairings_remain_ambiguous(self):
        group = next(g for g in self.findings["raw_gain_families"]
                     if "type_id" in "".join(g["symbol_family"]))
        self.assertEqual(len(group["linux_symbols"]), 2)
        self.assertEqual(len(group["captured_windows"]), 2)
        self.assertEqual(len(group["outgoing_calls"]), 4)
        self.assertEqual(self.findings["method_counts"]["linux"]["unique_inferred_entry_matches"], 66)

    def test_constant_decoder_preserves_unsigned_high_bits(self):
        raw = self.capture[599768:599808]
        self.assertEqual(c.returned_words(raw),
                         dict(r0="0xb48b06e23bc32191", r1="0x802914a71efcf08e"))
        wrong = bytearray(raw)
        wrong[32] = 0x85
        with self.assertRaisesRegex(ValueError, "return pattern"):
            c.returned_words(wrong)
        with self.assertRaises(ValueError):
            c.returned_words(raw[:-1])

    def test_intrinsic_gains_are_call_displacements_only(self):
        groups = [g for g in self.findings["raw_gain_families"]
                  if "type_id" not in "".join(g["symbol_family"])]
        self.assertEqual(len(groups), 3)
        self.assertTrue(all(row["only_internal_call_displacements"]
                            for g in groups for row in g["cross_host_deltas"]))
        self.assertEqual(sorted(len(g["cross_host_deltas"][0]["changed_instructions"]) for g in groups),
                         [1, 1, 11])

    def test_scalar_change_is_not_classified_as_call_layout(self):
        call = bytes.fromhex("8510000001000000")
        before = bytes.fromhex("b700000001000000") + call
        after = bytes.fromhex("b700000002000000") + call
        self.assertFalse(c.literal_delta(before, after, self.a)["only_internal_call_displacements"])

    def test_all_thirteen_direct_edges_have_raw_callees(self):
        rows = [r for g in self.findings["raw_gain_families"]
                for edge in g["outgoing_calls"] for r in edge["calls"]]
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r["raw_equal"] for r in rows))
        self.assertEqual({r["original_target"] for r in rows}, {697984, 706088, 706256, 706432})
        windows = self.findings["direct_callee_windows"]
        self.assertEqual(len(windows), 4)
        self.assertTrue(all(w["complete_inferred_window"] and not w["loader_relocation_overlaps"]
                            for w in windows))

    def test_callee_bytes_checked_separately_from_caller(self):
        code = self.capture[697984:703112]
        linux = (REPO / c.RUN / "candidate.so").read_bytes()
        symbols = self.a.functions(self.elf.Elf((REPO / c.RUN / "unstripped.so").read_bytes()))
        changed = bytearray(self.capture)
        changed[706256] ^= 1
        rows = c.raw_callees(code, 529880, 697984, linux,
                            self.elf.Elf(bytes(changed)), symbols, self.ctx, self.a)
        self.assertTrue(any(not r["raw_equal"] for r in rows if r["original_target"] == 706256))
        self.assertTrue(all(r["raw_equal"] for r in rows if r["original_target"] != 706256))

    def test_type_id_starts_need_relocated_pointer_evidence(self):
        self.assertFalse(self.ctx["calls"].get(599768))
        self.assertFalse(self.ctx["calls"].get(666624))
        self.assertEqual(self.ctx["pointers"][599768][0]["file_offset"], 728232)
        self.assertEqual(self.ctx["pointers"][666624][0]["file_offset"], 731888)
        self.assertEqual(self.ctx["pointers"][666664][0]["file_offset"], 732032)
        changed = self.changed_relocation(728232)
        ctx = c.pointer_entries(changed, self.a)
        self.assertFalse(c.window_evidence(changed, 599768, 40, ctx, self.a)["complete_inferred_window"])

    def test_nonzero_low_word_is_not_accepted_as_high_word_pointer(self):
        raw = bytearray(self.capture)
        raw[728232] = 1
        ctx = c.pointer_entries(self.elf.Elf(bytes(raw)), self.a)
        self.assertNotIn(599768, ctx["pointers"])

    def test_lddw_continuation_is_not_an_entry(self):
        raw = bytearray(self.capture)
        struct.pack_into("<Q", raw, 728232, 599776 << 32)
        ctx = c.pointer_entries(self.elf.Elf(bytes(raw)), self.a)
        self.assertNotIn(599776, ctx["entries"])

    def test_ten_negatives_preserved(self):
        rows = self.findings["linux_negatives"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(sum("drop_in_place" in "".join(r["names"]) for r in rows), 8)
        self.assertEqual(sum("RawVec" in "".join(r["names"]) or "finish_grow" in "".join(r["names"])
                             for r in rows), 2)

    def test_changed_input_rejected_before_analysis(self):
        with self.relocated() as root:
            path = root / c.RUN / "candidate.so"
            raw = bytearray(path.read_bytes())
            raw[441464] ^= 1
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "identity differs"):
                v.check_inputs(HERE, root)

    def test_rewritten_old_baseline_does_not_pass(self):
        with self.relocated() as root:
            path = root / c.DARWIN / "helper-results.json"
            data = json.loads(path.read_bytes())
            data["builds"]["v154"]["summary"]["entry_bounded_raw_exact_matches"] = 23
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Frozen Darwin baseline differs"):
                c.frozen_comparison(root)

    def test_canonical_report_paths(self):
        ids = [self.result["original"]] + [b[k] for b in self.result["builds"].values()
                                           for k in ("candidate", "symbol_source")]
        self.assertTrue(all("\\" not in row["path"] for row in ids))

    def test_forged_findings_rejected(self):
        changed = copy.deepcopy(self.findings)
        changed["distinct_raw_capture_ranges"]["gained"] = []
        actual = v.read
        def read(path):
            return changed if path.name == "findings.json" else actual(path)
        with mock.patch.object(v, "read", side_effect=read):
            with self.assertRaisesRegex(ValueError, "findings differ"):
                v.verify(HERE, REPO)

    def test_isolated_cli_with_only_pinned_inputs(self):
        with self.relocated() as root:
            result = subprocess.run([sys.executable, "-I", str(HERE / "verify.py"),
                                     "--repo", str(root)], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["distinct_raw_capture_ranges"]["linux"], 23)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=REPO)
    args, rest = parser.parse_known_args()
    REPO = args.repo
    unittest.main(argv=[sys.argv[0]] + rest)
