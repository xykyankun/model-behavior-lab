# Standard benchmark prompt experiment

**Status: completed on September 10, 2026.** Read the [full report](REPORT.md).

| Batch | Unique questions | Scheduled cells | Completed model sessions | Usable observations | Infrastructure exclusions |
|---|---:|---:|---:|---:|---:|
| Pilot | 4 | 24 | 24 | 24 | 0 |
| Main | 24 | 144 | 143 | 133 | 11 |

There are no unattempted cells. A launch failure has a retained record but no
completed model session. Ten other cells were excluded uniformly because the
Code Mode host was unavailable, including sessions that made no tool call. No
failed attempt was retried or replaced. See [provenance.json](provenance.json).

In usable observations, both models used no visible task-specific program under
neutral/no-code prompts and used an executed Python program under the explicit
code request. 132/133 usable main answers were correct (24/24 in the separate pilot). The narrow sample, near-ceiling scores,
shared custom base and model-dependent developer context prevent general model
rankings or equivalence claims. The report quantifies uncertainty and missingness.

## Sources and design

[GSM8K test](https://github.com/openai/grade-school-math) contains 1,319 examples;
[BIG-Bench Hard](https://github.com/suzgunmirac/BIG-Bench-Hard) word sorting,
object counting and logical deduction with three objects contain 250 each.
The [manifest](../../behavior_lab/sources.json) pins revisions and byte hashes;
[MIT notices](../../third_party) are retained. These are standard datasets used
with an adapted zero-shot/tool-enabled protocol, not official benchmark scores.

The pilot samples one question per source (seed 20260910). The disjoint main
sample selects six per source (seed 20260911). Each crosses two models and three
method prompts, one generation per cell, in frozen randomized order. Exact
questions, targets, prompts, models, effort and stopping rules are in
[protocol.json](protocol.json) and [main-protocol.json](main-protocol.json).
Targets are used by the scorer and are not inserted into task prompts/workspaces.

The main primary contrast is the paired neutral-prompt code-candidate rate,
Astra minus Sol. It retains 22 complete question pairs, with equal weight per
retained question; missingness changes source weights. Other prompts, accuracy,
resource use, source breakdowns and trace audits are exploratory. The four pilot
questions are not pooled with the main sample for inference.

## Reproduce offline

From the repository root, without model calls:

```bash
python3 -m unittest discover -s tests -v
python3 studies/standard-benchmarks/verify.py
python3 studies/standard-benchmarks/reproduce.py --check
```

The [public trial records](main-trials.json), [audit labels](main-audit.json),
[analysis](analysis.json) and [checksums](checksums.json) support offline review.
Audit labels were supplied by one assistant, not independent blinded annotators.
The automatic metric is a versioned inline-interpreter/awk candidate proxy.
The audit checks visible programs separately; neither measures code necessity.

To check exact question selection against the complete pinned source files:

```bash
python3 -m behavior_lab fetch private-runs/cache
python3 studies/standard-benchmarks/verify.py --cache private-runs/cache
```

For new model calls, follow [RUNNING.md](../../docs/RUNNING.md). A new run consumes
Codex usage and produces new stochastic observations. No personal conversation
history or previous synthetic-study results are used. Private raw logs, host
instruction bodies, credentials, local paths and session IDs are not published.
Prior-study files were removed from the current tree; clearing old public Git
history still awaits separate repository-deletion confirmation.
