import argparse
import json
from pathlib import Path

from .protocol import seal
from .runner import load_results, run_plan
from .statistics import paired_summary


def main():
    parser = argparse.ArgumentParser(description="Reproducible model behavior experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Seal a randomized protocol without calling a model")
    plan.add_argument("spec")
    plan.add_argument("output")
    run = sub.add_parser("run", help="Execute trusted synthetic trials; logs remain private")
    run.add_argument("plan")
    run.add_argument("output")
    run.add_argument("--max-runs", type=int, default=1)
    run.add_argument("--codex", default="codex")
    run.add_argument("--externally-sandboxed", action="store_true",
                     help="Omit nested sandbox ONLY when the parent/container enforces isolation")
    analyze = sub.add_parser("analyze", help="Analyze public rows, one condition at a time")
    analyze.add_argument("rows")
    analyze.add_argument("--condition", default="default")
    analyze.add_argument("--models", nargs=2, required=True)
    analyze.add_argument("--metric", default="aux_code_with_awk")
    analyze.add_argument("--exclude-controls", action="store_true")
    args = parser.parse_args()
    if args.command == "plan":
        result = seal(json.loads(Path(args.spec).read_text(encoding="utf-8")), args.output)
        print(json.dumps({"sha256": result["sha256"], "trials": len(result["jobs"])}))
    elif args.command == "run":
        run_plan(args.plan, args.output, args.max_runs, args.codex, args.externally_sandboxed)
    else:
        path = Path(args.rows)
        rows = load_results(path) if path.is_dir() else json.loads(path.read_text(encoding="utf-8"))
        rows = [r for r in rows if r["condition"] == args.condition and
                (not args.exclude_controls or r["category"] != "explicit_code")]
        print(json.dumps(paired_summary(rows, *args.models, metric=args.metric), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
