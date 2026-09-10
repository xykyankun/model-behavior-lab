# Public benchmark prompt pilot

**Status: pilot collection started; main protocol frozen before main collection.**

The sealed protocol samples one question from each of four public benchmark
sources, then crosses two models with three prompt conditions: 24 scheduled
attempts and four unique questions. This is a smoke/prompt-manipulation pilot,
not a sufficiently powered study of general model behavior.

Sources contain 1,319 GSM8K test examples and 250 examples each from BBH word
sorting, object counting and logical deduction with three objects. The source
manifest pins exact revisions and SHA-256 checksums. Source indices are preserved
in every case. Upstream questions and targets are licensed under the accompanying
MIT notices. No private or personal conversation data is included.

The protocol contains exact prompts, reference targets, method conditions, model
IDs, reasoning effort, sampling seed, randomized order and stopping rule. Targets
are used only by the scorer, not inserted into task prompts or workspaces.

Verify the plan offline:

```bash
python3 studies/standard-benchmarks/verify.py
```

Re-verify the selected questions against the complete pinned public sources:

```bash
python3 -m behavior_lab fetch private-runs/cache
python3 studies/standard-benchmarks/verify.py --cache private-runs/cache
```

When results are available, report all 24 cells, failures, exact prompt hashes,
correctness and code-candidate rates separately by model, prompt and source.
Do not publish local host instruction bodies, credentials, session IDs or paths.
Do not treat standard-dataset names as proof of standard benchmark comparability.

## Independent main sample

`main-protocol.json` selects six questions per source with seed 20260911:
24 questions, two models, three prompts, one attempt per cell = 144 attempts.
The sample has no overlap with the four pilot questions. It was fixed after one
successful infrastructure trial, before inspecting the remaining pilot outcomes.
Report it separately from the 24-attempt pilot; do not pool to improve significance.
The main primary contrast is the paired neutral-prompt code-candidate rate,
GPT-6 Astra minus GPT-5.6 Sol, with equal weight per question and source. Other
prompts, accuracy, format, latency, usage, and source subgroups are exploratory.
Keep the same stopping rule: attempt every cell once; retain failures; do not
add questions or retries in response to results. This is a limited exploratory
study, not a powered confirmatory test or an official benchmark submission.
