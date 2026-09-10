# Model Behavior Lab

Reproducible experiments about how models solve tasks: method choice, instruction
following, correctness, and resource use. English-only research materials, public
benchmark data, and explicit prompt interventions. Python 3.9+.

**First question: Does GPT-6 Astra use more auxiliary code than GPT-5.6 Sol?**
The repository defines a testable protocol; it does not assume the answer.
No personal conversations or locally collected chat-history datasets are used.

## Public benchmark sources

| Source | Available examples | Task |
|---|---:|---|
| [GSM8K test](https://github.com/openai/grade-school-math) | 1,319 | Arithmetic word problems |
| [BBH word sorting](https://github.com/suzgunmirac/BIG-Bench-Hard) | 250 | Lexicographic sorting |
| BBH object counting | 250 | Category counting |
| BBH logical deduction, three objects | 250 | Relational reasoning |

Source commits and SHA-256 checksums are pinned in
[the source manifest](behavior_lab/sources.json). Both upstream repositories use
MIT licenses; copies are in [third_party](third_party).

These are standard **datasets**, evaluated through an **adapted zero-shot,
tool-enabled protocol**. The scores are not directly comparable to official
GSM8K/BBH scores, including BBH's few-shot chain-of-thought setup. Public benchmarks
may also have appeared in training data.

## Prompt experiment

Every selected question is paired across two models and three method instructions:

| Condition | Exact method instruction | Interpretation |
|---|---|---|
| `neutral` | Choose the method you consider appropriate. | Spontaneous method choice |
| `no_code` | Solve without writing or executing any task-specific program. | No-code instruction following |
| `code_preferred` | Write and execute a short program to solve or verify the answer. | Positive control for code use |

All arms share the same question, answer-format instruction, base instruction and
reasoning setting. Effective host/tool context is recorded by hash and may still
differ between models. See [prompt analysis](docs/PROMPTS.md) and
[methodology](docs/METHODOLOGY.md) for causal limits.

## Reproduce or extend

```bash
python3 -m unittest discover -s tests -v
python3 studies/standard-benchmarks/verify.py
mkdir -p private-runs
python3 -m behavior_lab fetch private-runs/cache
python3 -m behavior_lab benchmark-plan private-runs/cache private-runs/plan.json \
  --models gpt-5.6-sol gpt-6-astra --per-source 25 --repeats 1
python3 -m behavior_lab run private-runs/plan.json private-runs/results --max-runs 1
```

Planning makes no model calls. Running uses your local Codex login and consumes
usage. The example above schedules 600 attempts; the runner executes at most one
per invocation unless you explicitly raise `--max-runs`. `--per-source 0` selects
all 2,069 examples: 12,414 attempts for two models, three prompts and one repeat.
Do not treat these planned counts as completed experiments. Inspect the first
trial before continuing; [RUNNING.md](docs/RUNNING.md) shows how to resume and
analyze complete matched pairs.

A [24-attempt pilot protocol](studies/standard-benchmarks/protocol.json) selects
one question per source. It is an infrastructure/prompt manipulation check, far
too small for a population-level model comparison. Study status and any collected
results are documented in [the study card](studies/standard-benchmarks/README.md).

The primary automatic behavior measure is a versioned inline interpreter/awk
**candidate proxy**, not a complete semantic measure of all programming.
Correctness and output-format compliance are separate fields. More code is not
inherently better or worse. Missing telemetry is not scored as “no code”.

Read [RUNNING.md](docs/RUNNING.md) before executing agents. Raw logs remain private;
public results must exclude host instructions, credentials and local paths.
For larger-scale execution, consider [Inspect](https://inspect.aisi.org.uk/).
Contributions and null findings are welcome: [CONTRIBUTING.md](CONTRIBUTING.md).

License: [MIT](LICENSE), with upstream notices retained. No model ranking is claimed.
