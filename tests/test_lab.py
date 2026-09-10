import os
import json
import tempfile
import unittest
from pathlib import Path

from behavior_lab.metrics import candidates
from behavior_lab.protocol import load_plan, safe_relative, seal, validate
from behavior_lab.runner import collect, load_results, run_plan
from behavior_lab.statistics import paired_summary, planning_sample_size


class StatisticsTests(unittest.TestCase):
    def rows(self, diffs):
        return [{"case": str(i), "model": m, "repeat": 1, "condition": "x", "valid": True,
                 "aux_code_with_awk": bool(value)}
                for i, (a, b) in enumerate(diffs) for m, value in (("a", a), ("b", b))]

    def test_exact_null_and_known_test(self):
        null = paired_summary(self.rows([(0, 0), (1, 1)]), "a", "b", draws=100)
        self.assertEqual(null["sign_flip_p_two_sided"], 1)
        known = paired_summary(self.rows([(0, 1)] * 3), "a", "b", draws=100)
        self.assertEqual(known["sign_flip_p_two_sided"], .25)
        self.assertEqual(known["difference_b_minus_a"], 1)

    def test_symmetry_and_repeat_invariance(self):
        rows = self.rows([(0, 1), (0, 0), (1, 0), (0, 1)])
        a = paired_summary(rows, "a", "b", draws=100)
        b = paired_summary(rows, "b", "a", draws=100)
        self.assertEqual(a["difference_b_minus_a"], -b["difference_b_minus_a"])
        self.assertEqual(a["sign_flip_p_two_sided"], b["sign_flip_p_two_sided"])
        duplicated = rows + [{**r, "repeat": 2} for r in rows]
        self.assertEqual(a, paired_summary(duplicated, "a", "b", draws=100))

    def test_missing_is_not_negative(self):
        rows = self.rows([(0, 1), (0, 1)])
        rows[0]["valid"] = False
        self.assertEqual(paired_summary(rows, "a", "b", draws=100)["excluded_tasks"], ["0"])
        with self.assertRaises(ValueError):
            paired_summary(rows + [rows[1]], "a", "b", draws=100)
        rows[0]["condition"] = "other"
        with self.assertRaises(ValueError):
            paired_summary(rows, "a", "b", draws=100)

    def test_planning(self):
        self.assertGreater(planning_sample_size(), 100)
        with self.assertRaises(ValueError):
            planning_sample_size(.2, .2)


class ProtocolTests(unittest.TestCase):
    def spec(self):
        return {"schema_version": 1, "models": ["a", "b"], "seed": 7, "repeats": 2,
                "timeout_seconds": 10, "conditions": [{"id": "default"}],
                "cases": [{"id": "one", "prompt": "hello", "files": {"x.txt": "abc"}}]}

    def test_seal_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plan.json"
            plan = seal(self.spec(), p)
            self.assertEqual(len(load_plan(p)["jobs"]), 4)
            self.assertEqual(plan["jobs"][0]["id"], "t0001")
            with self.assertRaises(FileExistsError):
                seal(self.spec(), p)
            plan["spec"]["cases"][0]["prompt"] = "changed"
            p.write_text(json.dumps(plan))
            with self.assertRaises(ValueError):
                load_plan(p)

    def test_path_traversal_and_hidden_configs(self):
        for name in ("../secret", "/tmp/secret", "x/../../secret", "C:\\secret", ".codex/config.toml", "."):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_relative(name)
        self.assertEqual(str(safe_relative("a/b.txt")), "a/b.txt")

    def test_invalid_condition_rejected_before_launch(self):
        spec = self.spec()
        spec["conditions"][0]["user_suffix"] = {"not": "text"}
        with self.assertRaises(ValueError):
            validate(spec)


class TelemetryTests(unittest.TestCase):
    def raw(self):
        return [{"type": "session_meta", "payload": {"base_instructions": "base"}},
                {"type": "turn_context", "payload": {"model": "a"}},
                {"type": "event_msg", "payload": {"type": "task_complete"}}]

    def test_true_zero_and_missing_logs(self):
        events = [{"type": "turn.completed"}]
        self.assertIs(collect(events, self.raw(), "a", 0)["aux_code_with_awk"], False)
        for raw, rc in (([], 0), (self.raw(), 1), (self.raw()[:-1], 0)):
            self.assertIsNone(collect(events, raw, "a", rc)["aux_code_with_awk"])
        self.assertFalse(collect(events, self.raw(), "b", 0)["valid"])
        self.assertFalse(collect(events, self.raw(), "a", 0, 1)["valid"])
        missing_context = self.raw()
        missing_context[0]["payload"] = {}
        self.assertFalse(collect(events, missing_context, "a", 0)["valid"])

    def test_unavailable_tool_host_is_not_a_valid_zero(self):
        events = [{"type":"turn.completed"}, {"type":"item.completed", "item":{
            "type":"error", "message":"Code Mode is unavailable because the host executable was not found."}}]
        result = collect(events, self.raw(), "a", 0)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["aux_code_with_awk"])
        events[1]["item"]["message"] = "Under-development features enabled: skip_host_skill_discovery."
        self.assertTrue(collect(events, self.raw(), "a", 0)["valid"])

    def test_nested_transport_exclusion_and_language_sensitivity(self):
        def score(body):
            return candidates([{"name": "functions.exec", "body": body}])
        self.assertFalse(score('text(await tools.exec_command({cmd: "cat a.json"}))')["aux_code_with_awk"])
        self.assertTrue(score("awk -F, '{s+=$2*$3} END{print s}' x.csv")["aux_code_with_awk"])
        self.assertFalse(score("awk -F, '{print $1}' x.csv")["inline_script"])
        for command in ("python3 - <<'PY'\nprint(2)\nPY", "node --input-type=module -e '1+1'", "perl -pi -e 's/a/b/' x", "ruby -rjson -e 'puts 1'"):
            self.assertTrue(score(command)["inline_script"], command)
        self.assertFalse(score("python3 existing.py")["inline_script"])


class RunnerIntegrationTests(unittest.TestCase):
    def test_failed_cli_is_retained_and_resume_preserves_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ProtocolTests().spec()
            seal(spec, root / "plan.json")
            fake = root / "fake-codex"
            fake.write_text("#!/bin/sh\nif [ \"$1\" = '--version' ]; then echo 'fake-cli'; exit 0; fi\nexit 7\n")
            fake.chmod(0o700)
            run_plan(root / "plan.json", root / "results", max_runs=1, codex=str(fake))
            rows = load_results(root / "results")
            self.assertEqual(len(rows), 4)
            self.assertEqual(sum(r["status"] == "not_completed" for r in rows), 3)
            self.assertEqual(rows[0]["status"], "error")
            self.assertIsNone(rows[0]["aux_code_with_awk"])
            run_plan(root / "plan.json", root / "results", max_runs=1, codex=str(fake))
            rows = load_results(root / "results")
            self.assertEqual(sum(r["status"] == "error" for r in rows), 2)
            self.assertFalse((root / "results/runner.lock").exists())
            self.assertEqual((root / "results/t0001/workspace/x.txt").read_text(), "abc")
            rowpath = root / "results/t0001/result.json"
            altered = json.loads(rowpath.read_text())
            altered["model"] = "wrong-model"
            rowpath.write_text(json.dumps(altered))
            with self.assertRaises(ValueError):
                load_results(root / "results")

    def test_launch_failure_is_a_missing_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            seal(ProtocolTests().spec(), root / "plan.json")
            fake = root / "fake-codex"
            fake.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo fake; rm -- "$0"; exit 0; fi\nexit 1\n')
            fake.chmod(0o700)
            run_plan(root / "plan.json", root / "results", max_runs=1, codex=str(fake))
            row = load_results(root / "results")[0]
            self.assertEqual(row["status"], "launch_error")
            self.assertEqual(row["launch_error"]["errno"], 2)
            self.assertFalse(row["valid"])
            self.assertIsNone(row["aux_code_with_awk"])
            self.assertFalse((root / "results/runner.lock").exists())

    def test_timeout_and_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = ProtocolTests().spec()
            spec["timeout_seconds"] = 1
            seal(spec, root / "plan.json")
            fake = root / "fake-codex"
            fake.write_text("#!/bin/sh\nif [ \"$1\" = '--version' ]; then echo fake; exit 0; fi\nsleep 10\n")
            fake.chmod(0o700)
            run_plan(root / "plan.json", root / "results", max_runs=1, codex=str(fake))
            self.assertEqual(load_results(root / "results")[0]["status"], "timeout")
            lock = root / "results/runner.lock"
            lock.write_text(str(os.getpid()))
            with self.assertRaises(FileExistsError):
                run_plan(root / "plan.json", root / "results", codex=str(fake))
            self.assertTrue(lock.exists())


if __name__ == "__main__":
    unittest.main()
