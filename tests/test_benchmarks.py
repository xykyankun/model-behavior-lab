import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from behavior_lab.benchmarks import load_cases, prepare, score_answer
from behavior_lab.protocol import load_plan


class AnswerScoringTests(unittest.TestCase):
    def test_decimal_equality_and_strict_final_line(self):
        case = {"answer_kind": "number", "target": "1000"}
        self.assertTrue(score_answer("Explanation.\nFINAL: 1,000.00", case)["correct"])
        for text in ("1000", "FINAL: 1000 dollars", "FINAL: 1000\nAnother sentence.", "FINAL: NaN"):
            result = score_answer(text, case)
            self.assertFalse(result["correct"], text)
            self.assertFalse(result["format_compliant"], text)
        result = score_answer("FINAL: 999", case)
        self.assertTrue(result["format_compliant"])
        self.assertFalse(result["correct"])

    def test_choice_and_word_order(self):
        choice = {"answer_kind": "choice", "target": "(B)"}
        self.assertTrue(score_answer("FINAL: (B)", choice)["correct"])
        self.assertFalse(score_answer("FINAL: (A)", choice)["correct"])
        self.assertFalse(score_answer("FINAL: B", choice)["format_compliant"])
        words = {"answer_kind": "words", "target": "apple pear plum"}
        self.assertTrue(score_answer("FINAL: apple pear plum", words)["correct"])
        self.assertFalse(score_answer("FINAL: apple plum pear", words)["correct"])
        self.assertFalse(score_answer("FINAL: apple, pear, plum", words)["format_compliant"])


class SamplingTests(unittest.TestCase):
    def fixture(self, root):
        # Tiny parser fixtures only, never an experimental dataset.
        data = "\n".join(json.dumps({"question": "Question " + str(i), "answer": "Solution\n#### " + str(i)}) for i in range(10)).encode()
        (root / "data.jsonl").write_bytes(data)
        return [{"file": "data.jsonl", "dataset": "gsm8k", "id": "gsm8k_test",
                 "split": "test", "count": 10, "answer_kind": "number", "repo": "example/data",
                 "path": "data.jsonl", "commit": "a" * 40, "sha256": hashlib.sha256(data).hexdigest()}]

    def test_deterministic_selection_no_gold_in_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("behavior_lab.benchmarks.source_manifest", return_value=self.fixture(root)):
                a = load_cases(root, 3, 42)
                self.assertEqual(a, load_cases(root, 3, 42))
                self.assertEqual(len({c["source"]["index"] for c in a}), 3)
                self.assertEqual(len(load_cases(root, 0, 42)), 10)
                prepare(root, root / "plan.json", ["a", "b"], per_source=3)
                plan = load_plan(root / "plan.json")
                self.assertEqual(len(plan["jobs"]), 18)
                self.assertTrue(all("Solution" not in c["prompt"] for c in plan["spec"]["cases"]))
                self.assertEqual(len({c["base_instructions"] for c in plan["spec"]["conditions"]}), 1)
                with self.assertRaises(ValueError):
                    load_cases(root, 11)
                (root / "data.jsonl").write_text("tampered")
                with self.assertRaises(ValueError):
                    load_cases(root, 1)
