"""Offline tests for the case table checker. Run:  python -m unittest discover tests"""

import tempfile
import unittest
from pathlib import Path

from src.cases import load_cases, validate


def row(case_id="c1", split="test", penn="a.txt", rwth="b.txt", label="reject", ltype="real", source="x"):
    return {
        "case_id": case_id, "split": split, "penn_doc": penn, "rwth_doc": rwth,
        "expected_recommendation": label, "label_type": ltype, "label_source": source, "notes": "",
    }


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self.tmp.name)
        for name in ("a.txt", "b.txt", "c.txt"):
            (self.docs / name).write_text("text", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, rows):
        return validate(rows, self.docs)

    def test_clean_table_has_no_errors(self):
        errors, _ = self.check([row("c1"), row("c2", rwth="c.txt")])
        self.assertEqual(errors, [])

    def test_duplicate_id_and_duplicate_pair(self):
        errors, _ = self.check([row("c1"), row("c1")])
        self.assertTrue(any("duplicate case_id" in e for e in errors))
        self.assertTrue(any("same document pair" in e for e in errors))

    def test_bad_values_and_missing_file(self):
        errors, _ = self.check([row("c1", split="train", label="maybe", ltype="fake", penn="zzz.txt", source="")])
        text = " ".join(errors)
        for part in ("split must be", "expected_recommendation must be", "label_type must be", "file not found", "label_source is empty"):
            self.assertIn(part, text)

    def test_warns_when_too_few_or_unbalanced(self):
        _, warnings = self.check([row("c1"), row("c2", rwth="c.txt")])
        text = " ".join(warnings)
        self.assertIn("only 2 test cases", text)
        self.assertIn("unbalanced", text)

    def test_real_table_loads(self):
        rows = load_cases()
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(validate(rows)[0], [])


if __name__ == "__main__":
    unittest.main()
