"""Content-addressed run plans; sealing is local, not independent registration."""

import datetime
import hashlib
import json
import random
import re
from pathlib import Path, PurePosixPath


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def safe_relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "\\" in name or p == PurePosixPath("."):
        raise ValueError("Fixture path must stay inside the workspace")
    if any(part.startswith(".") for part in p.parts):
        raise ValueError("Hidden fixture paths are disallowed")
    return p


def validate(spec):
    if spec.get("schema_version") != 1:
        raise ValueError("Unsupported protocol schema")
    if type(spec.get("repeats")) is not int or not 1 <= spec["repeats"] <= 100:
        raise ValueError("repeats must be 1..100")
    if not 1 <= spec.get("timeout_seconds", 0) <= 3600:
        raise ValueError("timeout_seconds must be 1..3600")
    if type(spec.get("seed")) is not int:
        raise ValueError("seed must be an integer")
    if spec.get("effort", "high") not in ("low", "medium", "high", "xhigh", "max", "ultra"):
        raise ValueError("Unsupported reasoning effort")
    for key in ("models", "conditions", "cases"):
        if not isinstance(spec.get(key), list) or not spec[key]:
            raise ValueError("Nonempty models, conditions and cases required")
    if len(set(spec["models"])) != len(spec["models"]):
        raise ValueError("Duplicate models")
    if any(not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:/-]*", m) for m in spec["models"]):
        raise ValueError("Invalid model identifier")
    for collection in (spec["conditions"], spec["cases"]):
        ids = [x["id"] for x in collection]
        if len(set(ids)) != len(ids) or any(not re.fullmatch(r"[a-z0-9_]+", x) for x in ids):
            raise ValueError("IDs must be unique lowercase identifiers")
    for case in spec["cases"]:
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            raise ValueError("Nonempty prompt required")
        for name, content in case.get("files", {}).items():
            safe_relative(name)
            if not isinstance(content, str):
                raise ValueError("Fixtures must contain text")
    for condition in spec["conditions"]:
        for key in ("user_suffix", "base_instructions"):
            if key in condition and not isinstance(condition[key], str):
                raise ValueError("Condition instructions must contain text")


def seal(spec, destination):
    validate(spec)
    jobs = [{"case": c["id"], "model": m, "condition": cond["id"], "repeat": r}
            for c in spec["cases"] for m in spec["models"]
            for cond in spec["conditions"] for r in range(1, spec["repeats"] + 1)]
    random.Random(spec["seed"]).shuffle(jobs)
    for i, job in enumerate(jobs):
        job["id"] = "t%04d" % (i + 1)
    payload = {"spec": spec, "jobs": jobs,
               "sealed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    result = {**payload, "sha256": digest(payload)}
    with Path(destination).open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = {k: v for k, v in plan.items() if k != "sha256"}
    if digest(payload) != plan.get("sha256"):
        raise ValueError("Plan content hash mismatch")
    validate(plan["spec"])
    expected = {(c["id"], m, x["id"], r) for c in plan["spec"]["cases"]
                for m in plan["spec"]["models"] for x in plan["spec"]["conditions"]
                for r in range(1, plan["spec"]["repeats"] + 1)}
    actual = [(j["case"], j["model"], j["condition"], j["repeat"]) for j in plan["jobs"]]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Plan is not the complete factorial design")
    if [j["id"] for j in plan["jobs"]] != ["t%04d" % (i + 1) for i in range(len(actual))]:
        raise ValueError("Trial IDs must be ordered opaque identifiers")
    return plan
