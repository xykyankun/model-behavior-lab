import argparse
import json
from pathlib import Path

from .protocol import seal
from .runner import load_results, run_plan
from .statistics import paired_summary
from .benchmarks import fetch_sources, prepare


def main():
    parser = argparse.ArgumentParser(description="Reproducible model behavior experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="Download and checksum pinned public benchmark sources")
    fetch.add_argument("cache")
    fetch.add_argument("--ca-file")
    bench = sub.add_parser("benchmark-plan", help="Seal a model-by-prompt experiment on standard datasets")
    bench.add_argument("cache")
    bench.add_argument("output")
    bench.add_argument("--models", nargs="+", required=True)
    bench.add_argument("--per-source", type=int, default=1, help="Questions per source; 0 selects all")
    bench.add_argument("--repeats", type=int, default=1)
    bench.add_argument("--seed", type=int, default=20260910)
    plan = sub.add_parser("plan", help="Seal a randomized protocol without calling a model")
    plan.add_argument("spec")
    plan.add_argument("output")
    run = sub.add_parser("run", help="Execute reviewed benchmark trials; logs remain private")
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
    if args.command == "fetch":
        fetch_sources(args.cache, args.ca_file)
        print("Pinned public sources verified.")
    elif args.command == "benchmark-plan":
        result = prepare(args.cache, args.output, args.models, args.per_source, args.repeats, args.seed)
        print(json.dumps({"sha256": result["sha256"], "trials": len(result["jobs"])}))
    elif args.command == "plan":
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
