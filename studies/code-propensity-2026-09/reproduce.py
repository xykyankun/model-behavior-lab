"""Recompute the public study, offline. No private history is read."""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from behavior_lab.metrics import candidates
from behavior_lab.statistics import paired_summary, planning_sample_size


def compute():
    rows = json.loads((ROOT / "trials.json").read_text(encoding="utf-8"))
    assert len(rows) == 84 and len({r["id"] for r in rows}) == 84
    assert all(r["valid"] and r["status"] == "finished" and r["exit_code"] == 0 for r in rows)
    counts = defaultdict(lambda: [0, 0])
    cases = {c["id"] for c in json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))}
    for r in rows:
        assert r["case"] in cases
        assert r["observed_models"] == [r["model"]]
        assert candidates(r["calls"]) == {k: r[k] for k in candidates([])}
        key = " / ".join([r["condition"], r["category"], r["model"]])
        counts[key][0] += r["aux_code_with_awk"]
        counts[key][1] += 1
    analyses = {}
    for condition in ("default", "shared"):
        selected = [r for r in rows if r["condition"] == condition]
        for metric in ("aux_code_with_awk", "inline_script"):
            analyses[condition + "/" + metric] = paired_summary(selected, "gpt-5.6-sol", "gpt-6-astra", metric)
        if condition == "default":
            analyses["default/non_control"] = paired_summary(
                [r for r in selected if r["category"] != "explicit_code"], "gpt-5.6-sol", "gpt-6-astra")
    # Same 10 task pairs and same repeat for the partial base-instruction comparison.
    shared_cases = {r["case"] for r in rows if r["condition"] == "shared"}
    analyses["matched_default_repeat1"] = paired_summary(
        [r for r in rows if r["condition"] == "default" and r["repeat"] == 1 and r["case"] in shared_cases],
        "gpt-5.6-sol", "gpt-6-astra")
    return {"valid_trials": len(rows), "unique_tasks": len(cases),
            "category_counts": dict(sorted(counts.items())), "analyses": analyses,
            "planning_only_independent_samples_per_model_20_to_35_percent": planning_sample_size()}


def audit_public_data():
    # Defense in depth, not a universal privacy guarantee. Source data was allowlisted.
    patterns = [r"/Users/[A-Za-z0-9]", r"/home/[A-Za-z0-9]", r"\bgh[pousr]_[A-Za-z0-9]{20,}",
                r"\b(?:sk|qk|kgw)[-_][A-Za-z0-9_-]{16,}",
                r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"]
    for path in ROOT.glob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert not any(re.search(p, content) for p in patterns), "Possible private field in " + path.name


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    audit_public_data()
    result = compute()
    if args.check:
        assert result == json.loads((ROOT / "analysis.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "checksums.json").read_text(encoding="utf-8"))
        for name, expected in manifest.items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        print("84 trials recomputed; metrics, paired analyses, public-data scan and checksums match.")
    else:
        (ROOT / "analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(ROOT.glob("*.json")) if p.name != "checksums.json"}
        (ROOT / "checksums.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: {n: v[n] for n in ("matched_tasks", "difference_b_minus_a", "bootstrap_percentile_95", "sign_flip_p_two_sided")}
                          for k, v in result["analyses"].items()}, indent=2))
