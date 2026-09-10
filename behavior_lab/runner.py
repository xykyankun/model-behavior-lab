"""Codex CLI adapter. Runs reviewed benchmark tasks; logs are PRIVATE."""

import json
import os
import platform
import signal
import sqlite3
import subprocess
import time
from pathlib import Path

from .metrics import METRIC_VERSION, candidates
from .protocol import digest, load_plan, safe_relative
from .benchmarks import score_answer


def jsonl(path):
    result, malformed = [], 0
    if not path.exists():
        return [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    return result, malformed


def find_rollout(thread_id, codex_home):
    """Lookup only the experiment's exact thread; never sweep private transcripts."""
    for db in sorted(codex_home.glob("state_*.sqlite"), reverse=True):
        try:
            with sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True) as conn:
                row = conn.execute("SELECT rollout_path FROM threads WHERE id=?", (thread_id,)).fetchone()
            if row and Path(row[0]).is_file():
                return Path(row[0])
        except sqlite3.Error:
            continue
    return None


def collect(events, raw, requested_model, returncode, malformed=0):
    """Absent/incomplete telemetry produces null metrics, not a zero."""
    models, calls, bases, developers = [], [], [], []
    for event in raw:
        p = event.get("payload", {})
        if event.get("type") == "session_meta" and p.get("base_instructions") is not None:
            bases.append(digest(p.get("base_instructions")))
        if event.get("type") == "turn_context":
            models.append(p.get("model"))
        if event.get("type") == "response_item":
            if p.get("role") == "developer":
                developers.append(digest(p.get("content")))
            if p.get("type") in ("function_call", "custom_tool_call"):
                calls.append({"name": p.get("name"), "body": p.get("input", p.get("arguments", ""))})
    complete = any(e.get("type") == "turn.completed" for e in events)
    raw_complete = any(e.get("type") == "event_msg" and
                       e.get("payload", {}).get("type") in ("task_complete", "task_completed") for e in raw)
    valid = (returncode == 0 and complete and raw_complete and malformed == 0 and
             bool(models) and set(models) == {requested_model} and bool(bases))
    metrics = candidates(calls) if valid else {k: None for k in ("inline_script", "awk_code", "aux_code_with_awk")}
    usage = next((e.get("usage") for e in reversed(events) if e.get("type") == "turn.completed"), None)
    return {"valid": valid, "observed_models": sorted(set(models), key=str),
            "complete": complete, "raw_complete": raw_complete, "malformed_lines": malformed,
            "base_hashes": bases, "developer_hashes": developers, "calls": calls,
            "metric_version": METRIC_VERSION, "usage": usage, **metrics}


def run_plan(plan_path, output, max_runs=1, codex="codex", external_sandbox=False):
    if os.name != "posix":
        raise ValueError("CLI runner currently supports POSIX systems only")
    if max_runs < 1:
        raise ValueError("max_runs must be positive")
    plan = load_plan(plan_path)
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "runner.lock"
    with lock.open("x") as f:
        f.write(str(os.getpid()))
    try:
        stamp = root / "plan.json"
        if stamp.exists():
            if load_plan(stamp)["sha256"] != plan["sha256"]:
                raise ValueError("Output directory belongs to a different plan")
        else:
            if any(p.name != "runner.lock" for p in root.iterdir()):
                raise ValueError("Use an empty output directory")
            stamp.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        version = subprocess.run([codex, "--version"], capture_output=True, text=True, check=True).stdout.strip()
        count = 0
        for job in plan["jobs"]:
            trial = root / job["id"]
            if (trial / "result.json").exists():
                continue  # Failed attempts are also immutable; no selective retry.
            if trial.exists():
                raise ValueError("Incomplete attempt exists; inspect and record it before resuming")
            case = next(c for c in plan["spec"]["cases"] if c["id"] == job["case"])
            cond = next(c for c in plan["spec"]["conditions"] if c["id"] == job["condition"])
            workspace = trial / "workspace"
            workspace.mkdir(parents=True)
            for name, content in case.get("files", {}).items():
                path = workspace / str(safe_relative(name))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            sandbox = "danger-full-access" if external_sandbox else "workspace-write"
            argv = [codex, "exec", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check",
                    "--thread-source", "behavior-lab", "-C", str(workspace), "-m", job["model"],
                    "-c", 'model_reasoning_effort=' + json.dumps(plan["spec"].get("effort", "high")),
                    "-c", "project_doc_max_bytes=0", "-s", sandbox, "--json", "-o", str(trial / "answer.txt")]
            for feature in ("memories", "plugins", "apps", "multi_agent", "hooks", "shell_snapshot"):
                argv += ["--disable", feature]
            argv += ["--enable", "skip_host_skill_discovery"]
            if cond.get("base_instructions"):
                instructions = trial / "base.txt"
                instructions.write_text(cond["base_instructions"], encoding="utf-8")
                argv += ["-c", "model_instructions_file=" + json.dumps(str(instructions))]
            argv += ["-"]
            env = os.environ.copy()
            (trial / "shell").mkdir()
            env["ZDOTDIR"] = str(trial / "shell")
            start = time.monotonic()
            status, rc = "finished", None
            with (trial / "events.jsonl").open("w") as out, (trial / "stderr.log").open("w") as err:
                p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=out, stderr=err, env=env,
                                     text=True, start_new_session=True)
                try:
                    p.communicate(case["prompt"] + cond.get("user_suffix", ""),
                                  timeout=plan["spec"]["timeout_seconds"])
                    rc = p.returncode
                    if rc != 0:
                        status = "error"
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    p.communicate()
                    status = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "interrupted"
                    rc = p.returncode
            events, errors = jsonl(trial / "events.jsonl")
            tid = next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None)
            home = Path(env.get("CODEX_HOME", str(Path.home() / ".codex")))
            rollout = find_rollout(tid, home) if tid else None
            raw, raw_errors = jsonl(rollout) if rollout else ([], 0)
            result = {**job, "category": case.get("category", "unspecified"),
                      "status": status, "exit_code": rc, "plan_sha256": plan["sha256"],
                      "cli_version": version, "platform": platform.platform(), "sandbox": sandbox,
                      "seconds": round(time.monotonic() - start, 3), "argv": argv,
                      "thread_id": tid, "rollout_path": str(rollout) if rollout else None,
                      **collect(events, raw, job["model"], rc, errors + raw_errors)}
            answer_path = trial / "answer.txt"
            result["answer"] = answer_path.read_text(encoding="utf-8") if answer_path.exists() else ""
            if "answer_kind" in case:
                result.update(score_answer(result["answer"], case) if result["valid"] else
                              {"correct": None, "format_compliant": None, "parsed_answer": None})
            (trial / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: result[k] for k in ("id", "status", "valid", "seconds")}), flush=True)
            count += 1
            if status == "interrupted" or count >= max_runs:
                break
    finally:
        lock.unlink()


def load_results(directory):
    """Include every scheduled job, so unattempted pairs cannot disappear."""
    root = Path(directory)
    plan = load_plan(root / "plan.json")
    rows = []
    expected_paths = {root / j["id"] / "result.json" for j in plan["jobs"]}
    if set(root.glob("*/result.json")) - expected_paths:
        raise ValueError("Unexpected result files outside plan")
    for job in plan["jobs"]:
        path = root / job["id"] / "result.json"
        category = next(c.get("category", "unspecified") for c in plan["spec"]["cases"] if c["id"] == job["case"])
        if path.exists():
            row = json.loads(path.read_text(encoding="utf-8"))
            if row.get("plan_sha256") != plan["sha256"] or any(row.get(k) != v for k, v in job.items()):
                raise ValueError("Result identity does not match sealed plan")
        else:
            row = {**job, "valid": False, "status": "not_completed", "category": category}
        rows.append(row)
    return rows
