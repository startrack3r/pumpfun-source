import re
import unittest
import probe


class InputTests(unittest.TestCase):
    def test_only_basic_block_order_changes(self):
        variants = probe.inputs()
        self.assertEqual(set(variants), {'near-error', 'far-error'})
        parsed = {}
        for name, raw in variants.items():
            text = raw.decode()
            sections = re.split(r'^([a-z_]+):\n', text, flags=re.M)
            blocks = {sections[i]: sections[i + 1].removesuffix('}\n').strip()
                      for i in range(1, len(sections), 2)}
            self.assertEqual(set(blocks), {'entry', 'remaining_check', 'initial_error', 'success', 'underflow_error'})
            parsed[name] = (sections[0], blocks)
        self.assertEqual(parsed['far-error'], parsed['near-error'])
        self.assertNotEqual(variants['far-error'], variants['near-error'])

    def test_controlled_remaining_check_and_error(self):
        for raw in probe.inputs().values():
            self.assertIn(b'%under = icmp ult i64 %remaining, %n', raw)
            self.assertIn(b'br i1 %under, label %underflow_error, label %success', raw)
            self.assertEqual(raw.count(b'store i64 86, ptr %out, align 8'), 2)

    def test_archive_and_image_are_content_pinned(self):
        self.assertEqual(probe.ARCHIVE_SHA, '8d5153589dbe19635affe937663cf4555a7e69a62d91ab4a1df064aaa8d5f066')
        self.assertTrue(probe.IMAGE.endswith('@sha256:43206149a565ec35da95b1a909f4714f5d5f0d8241c31df24189e517acd18467'))

    def test_tar_dot_prefix_is_not_a_different_member(self):
        self.assertEqual(probe.member_path('./llvm/bin/llc'), 'llvm/bin/llc')
        self.assertEqual(probe.member_path('version.md'), 'version.md')
        for name in ('../llc', '/llc', 'llvm\\llc'):
            with self.assertRaises(ValueError):
                probe.member_path(name)


if __name__ == '__main__':
    unittest.main()
