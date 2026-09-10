# Model Behavior Lab

把对模型的直觉，变成可以复算、反驳和改进的实验。

An open research workbench for observable model behavior: protocols, matched tasks,
tool traces, counterexamples, uncertainty, and explicit limits on conclusions.
Python 3.9+; offline analysis has no third-party dependencies.

**First study: Does GPT-6 use more code to solve problems?**

We observed more auxiliary-program candidates in GPT-6 Astra than GPT-5.6 Sol in
one user's Codex environment. The 84 synthetic trials do **not** establish a
general, model-intrinsic difference: tasks are few, prompts differ, and the
task-level exploratory test is inconclusive. Writing more code is not itself a
quality failure. These are local model identifiers, not an official benchmark.

| Evidence | GPT-5.6 Sol | GPT-6 Astra | What it supports |
|---|---:|---:|---|
| Completed historical turns | 241 / 1,500 (16.1%) | 50 / 133 (37.6%) | Observational association; private source corpus |
| Synthetic default condition | 7 / 32 (21.9%) | 12 / 32 (37.5%) | Difference on 16 selected tasks; paired exploratory p = .25 |
| Text / discussion / planning subset | 0 / 16 | 0 / 16 | Counterevidence to an indiscriminate coding tendency |
| File-reading / explanation subset | 2 / 8 | 4 / 8 | Difference concentrated in some file tasks |
| Small-edit subset | 3 / 6 | 6 / 6 | Additional validation programs were common |

Metric includes inline Python/Node/Ruby/Perl and awk candidates, **not all
programming**. In the CSV task both models wrote programs: Sol used awk, Astra
used Python. Treating awk as “no code” exaggerates the difference.

Read the [完整中文研究报告](studies/code-propensity-2026-09/REPORT.zh-CN.md),
[methodology](docs/METHODOLOGY.md), and [data card](studies/code-propensity-2026-09/DATA_CARD.md).

## Reproduce the published evidence offline

```bash
git clone https://github.com/xykyankun/model-behavior-lab.git
cd model-behavior-lab
python3 -m unittest discover -s tests -v
python3 studies/code-propensity-2026-09/reproduce.py --check
python3 -m behavior_lab analyze studies/code-propensity-2026-09/trials.json \
  --condition default --models gpt-5.6-sol gpt-6-astra --exclude-controls
```

This recomputes metrics and task-level statistics from the 84 published synthetic
trial records. It does not contact a model or reconstruct private history.
The historical aggregates cannot be independently rederived from this repository.

## Run a new experiment

```bash
mkdir -p private-runs
python3 -m behavior_lab plan \
  studies/code-propensity-2026-09/replication-spec.json private-runs/plan.json
python3 -m behavior_lab run private-runs/plan.json private-runs/results --max-runs 1
```

Planning makes no model calls. Running requires a logged-in, compatible Codex
CLI and consumes your usage. Start with one infrastructure check; the included
replication specification schedules **48 attempts**, not 48 completed results.
Its data has **not** been collected. The default limit is one attempt per command;
raise `--max-runs` to continue. Completed failures are retained and skipped on resume.

The runner uses `workspace-write` and trusted synthetic fixtures. Its logs remain
private and can contain host instructions and paths. Read [RUNNING.md](docs/RUNNING.md)
before running agents. The `--externally-sandboxed` option is only for an already
isolated parent/container that cannot install a nested sandbox; it is not a
general troubleshooting switch.

## What exists today

- Content-hashed, randomized plans and opaque trial directories.
- A Codex CLI adapter with timeout handling, model/context hashes and missing-data checks.
- Stable lexical proxies, paired task bootstrap intervals and sign-flip sensitivity tests.
- Synthetic prompts, fixtures, 84 answers and tool inputs, provenance and checksums.
- An exploratory case study, counterexamples and a prospective replication specification.

This is a research workbench, not a model ranking site. API-native adapters,
independent blinded annotation, causal prompt ablations and broad held-out task
sets are future work. See [CONTRIBUTING.md](CONTRIBUTING.md) to add another hypothesis.

For large agent evaluations, [Inspect](https://inspect.aisi.org.uk/) already
provides execution, logging and scoring infrastructure. This small project focuses
on the research question and local Codex traces; it does not replace Inspect or
[HELM](https://github.com/stanford-crfm/helm).

License: [MIT](LICENSE). Research results are exploratory and have not been peer reviewed.
