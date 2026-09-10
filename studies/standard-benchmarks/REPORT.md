# Does GPT-6 Astra use more auxiliary code than GPT-5.6 Sol?

Completed on September 10, 2026. Exploratory evidence from public standard datasets, with an adapted Codex protocol.

## Finding

**This study did not observe more spontaneous code use from GPT-6 Astra.** In every usable neutral and no-code trial, both models answered without a visible task-specific program. When explicitly asked to write and execute a program, both did so in every usable trial. 132/133 usable main answers were correct.

That is evidence of a strong response to the explicit method instruction on these sampled questions. It is **not evidence that the models are equivalent in general**, nor a test of ordinary Codex conversations: the experiment supplied a shared custom base prompt, used a small set of reasoning questions, and retained model-dependent developer context.

## Design and coverage

The main sample contains **24 questions and 144 planned attempts**: six questions from each of four sources, crossed with two models and three prompts, one attempt per cell. All 144 scheduled cells have a final record: **133 usable, 11 infrastructure exclusions, zero unattempted**. There are 143 completed model sessions; one CLI launch failed before a request began. A separate disjoint pilot contains four questions and 24 usable attempts. Across both batches there are 28 unique questions, 168 scheduled cells and 157 usable observations. These are not 168 independent questions.

The sources are [GSM8K test](https://github.com/openai/grade-school-math), and [BIG-Bench Hard](https://github.com/suzgunmirac/BIG-Bench-Hard) word sorting, object counting and logical deduction with three objects. The source files contain 2,069 available examples; we did not run all of them. Exact upstream commits, byte hashes, counts and MIT notices are in the [source manifest](../../behavior_lab/sources.json) and [third-party licenses](../../third_party). Selected questions are copied verbatim, with their original source indices in the sealed plans.

This is **standard-dataset-backed research, not an official benchmark score**. Zero-shot prompts, tool availability and method interventions differ from the published protocols. See the original [GSM8K paper](https://arxiv.org/abs/2110.14168) and [BBH paper](https://arxiv.org/abs/2210.09261).

Both batches had frozen samples, order, settings and one-attempt stopping rules before their collection. The [main protocol](main-protocol.json) was initially published in commit `07f7df84d6f0b2ea053dba759dfd2e5f6b3cc4cb` before main collection, after one pilot infrastructure check and before inspecting the remaining pilot outcomes. It uses seed 20260911 and SHA-256 `cecfd2806c3d3bb935b9624e21c35298bd54b612c5de39314a0853dcb7950d1c`. The seed controls sampling and order, not generation randomness. This was not an independently registered or power-calculated confirmatory study. The [provenance record](provenance.json) describes timing, analysis additions and incidents.

## Exact prompt manipulation

Each trial uses the same base text:

> You are an assistant solving the user's question. Follow the requested method and answer format. Work only on the supplied question. Do not browse the web or inspect files outside the current workspace.

The verbatim benchmark question is followed by a shared answer-format instruction and one method suffix:

| Condition | Exact method instruction |
|---|---|
| Neutral | Choose the method you consider appropriate. |
| No code | Solve without writing or executing any task-specific program. |
| Code preferred | Write and execute a short program to solve or verify the answer. |

The final line must be `FINAL: <answer>`. Reference targets are outside the child workspace and are never inserted into its prompt. This is not a hardened adversarial answer-isolation environment. Trials use fresh workspaces, reasoning effort `high`, and `workspace-write` sandboxing. [PROMPTS.md](../../docs/PROMPTS.md) distinguishes prompt interventions from claims about model weights.

## Main results

The automatic measure is the frozen `inline-interpreter-awk-v1` **code-candidate proxy**. It detects certain inline interpreter and awk patterns, not every possible program. Denominators below include only usable observations; infrastructure failures are not counted as no-code or wrong answers.

| Prompt | Model | Code candidates | Wilson 95% interval | Correct answers |
|---|---|---:|---:|---:|
| `neutral` | `gpt-5.6-sol` | 0/24 (0.0%) | 0.0% to 13.8% | 24/24 (100.0%) |
| `neutral` | `gpt-6-astra` | 0/22 (0.0%) | 0.0% to 14.9% | 22/22 (100.0%) |
| `no_code` | `gpt-5.6-sol` | 0/21 (0.0%) | 0.0% to 15.5% | 20/21 (95.2%) |
| `no_code` | `gpt-6-astra` | 0/23 (0.0%) | 0.0% to 14.3% | 23/23 (100.0%) |
| `code_preferred` | `gpt-5.6-sol` | 22/22 (100.0%) | 85.1% to 100.0% | 22/22 (100.0%) |
| `code_preferred` | `gpt-6-astra` | 21/21 (100.0%) | 84.5% to 100.0% | 21/21 (100.0%) |

Output-format compliance is 100% in every usable main cell. Correctness is a separate measure. [Trial-level data](main-trials.json) contain the answers, sanitized tool inputs and command outputs, scores, model/configuration evidence and all exclusions. [analysis.json](analysis.json) contains the full calculation.

Wilson intervals illustrate uncertainty in individual proportions under a binomial model. They do not model dependence within task families, and are not paired confidence intervals for the model difference. The [NIST description](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) documents the interval method.

### Paired model comparison

Only questions with usable observations for both models in that condition enter these comparisons. Each retained question gets equal weight; exclusions change the originally balanced source weights.

| Prompt | Complete question pairs | Sol code rate | Astra code rate | Astra minus Sol |
|---|---:|---:|---:|---:|
| `neutral` | 22 | 0.0% | 0.0% | +0.0 pp |
| `no_code` | 20 | 0.0% | 0.0% | +0.0 pp |
| `code_preferred` | 19 | 100.0% | 100.0% | +0.0 pp |

The primary neutral contrast is **+0.0 pp on 22 complete question pairs**, with no discordant pairs. The predeclared empirical bootstrap returns `[0, 0]`, and the exact sign-flip test returns p = 1. With all observed differences zero, the bootstrap is degenerate: **these outputs cannot establish equivalence or rule out a meaningful population difference**. No equivalence margin or confirmatory power target was specified.

As an exploratory prompt contrast, the 17 questions with all four required neutral/code-preferred cells show a +100 percentage-point code-use change for each model; the difference of changes is zero. The matched no-code contrast uses 18 questions and shows zero change for both. This positive control confirms that usable trials provided working program execution. It does not explain the contribution of the default Codex prompt, which was not tested.

### Missing-data sensitivity

Assigning every unusable planned cell either code or no-code gives the following worst-case bounds on the **planned-sample** Astra-minus-Sol difference. These are not sampling confidence intervals and not causal estimates.

| Prompt | Difference bounds |
|---|---:|
| `neutral` | +0.0 pp to +8.3 pp |
| `no_code` | -12.5 pp to +4.2 pp |
| `code_preferred` | -12.5 pp to +8.3 pp |

### Source breakdown

Each entry below is code-positive / usable, in the order **neutral; no code; code preferred**. Each source originally contributed six questions per model and condition. Full source-specific correctness counts are in `analysis.json`; these very small groups do not support separate rankings.

| Source | Sol | Astra |
|---|---|---|
| `bbh_logical_deduction_three_objects` | 0/6; 0/6; 6/6 | 0/6; 0/6; 6/6 |
| `bbh_object_counting` | 0/6; 0/6; 6/6 | 0/6; 0/5; 4/4 |
| `bbh_word_sorting` | 0/6; 0/4; 5/5 | 0/6; 0/6; 6/6 |
| `gsm8k_test` | 0/6; 0/5; 5/5 | 0/4; 0/6; 5/5 |

## Answer error inspection

The incorrect-answer records are listed below. They remain ordinary scored observations, not infrastructure exclusions. One error does not establish an accuracy advantage or a causal benefit from code.

| Trial | Model | Prompt | Case | Parsed answer | Reference |
|---|---|---|---|---|---|
| `t0107` | `gpt-5.6-sol` | `no_code` | `bbh_object_counting_0209` | 14 | 13 |

## Trace audit and what counts as code

A single assistant inspected every published final answer, tool input and command output, including excluded attempts. This audit is neither independent nor blinded, and it has no inter-rater agreement estimate. It is a check of the proxy against visible traces, not independent ground truth or an assessment of whether code was necessary.

For usable main observations, all **43** detected programs were Python programs that computed or verified the answer, with successful command execution. The audit found no additional visible programs missed by the proxy and no proxy disagreements. Neutral/no-code answers contained direct answers or mathematical explanations, not programs. Algebra and LaTeX were not labeled as programming; a JavaScript wrapper that only dispatched a tool was not counted as task logic. Labels are in [main-audit.json](main-audit.json).

Four excluded tool-host trials visibly authored program attempts but could not execute them. They remain in the trace data and audit, with execution marked false; one tried a JavaScript calculation after a Python attempt. The launch-failure trial has unknown program labels because no model ran. Excluded traces are not added to usable behavior rates.

The disjoint pilot showed the same visible pattern: for each model, neutral 0/4 code, no-code 0/4, and code-preferred 4/4. All 24 answers were correct. Its [records](pilot-trials.json) and [audit](pilot-audit.json) are separate; pilot and main were not pooled for inference.

## Infrastructure incidents and effective context

One main cell, `t0051`, failed before model launch when the global npm Codex executable was replaced during collection. Its exception and empty event files were used to reconstruct an explicit invalid record. It was not retried.

To continue with CLI version 0.153.4, the runner used a private copy of the installed desktop binary. The first recovery copy omitted its adjacent `codex-code-mode-host` helper: **our infrastructure error**. All ten cells `t0052` through `t0061` emitted a fatal tool-host startup diagnostic. Every one was excluded, including sessions that never attempted a tool call. A correct answer from the first recovery check did not establish tool availability. After the matching helper was copied, actual program commands succeeded starting at `t0062`. No failed cell was rerun or silently replaced. The collector now retains launch errors automatically and rejects the fatal startup diagnostic.

Every usable trial records the requested model ID, effort `high`, `workspace-write`, CLI session version 0.153.4 and exact shared base text. Within each model, normalized developer-context hashes are stable across the observed phases. **Developer context differs between models**: normalized content lengths are 9,923 / 2,335 / 307 characters for Sol and 11,305 / 2,501 / 307 for Astra. These lengths do not measure coding pressure. Hashes cover recorded base/developer content, not all tool schemas or hidden backend context. CLI IDs are not independent attestations of deployed weights. Version equality also cannot establish byte identity to the unavailable original npm binary. Hashes of the copied binary and helper are recorded in [provenance.json](provenance.json).

## Resource accounting

These are **descriptive CLI totals**, including available usage from excluded completed sessions. Input and cached-input fields are shown separately; cached input is not added again as extra input. Usage is unavailable for the launch-failure cell. No money estimate is made. Median elapsed time includes CLI startup, model-catalog refresh, network and tools. Pilot and main temporarily overlapped, so these numbers are not a model-speed comparison.

| Model | Prompt | Median elapsed seconds | Usage records | Input tokens | Cached input tokens | Output tokens |
|---|---|---:|---:|---:|---:|---:|
| `gpt-5.6-sol` | `neutral` | 23.2 | 24 | 249,279 | 175,360 | 1,751 |
| `gpt-5.6-sol` | `no_code` | 24.6 | 24 | 249,351 | 178,688 | 2,000 |
| `gpt-5.6-sol` | `code_preferred` | 34.5 | 24 | 525,518 | 399,744 | 5,146 |
| `gpt-6-astra` | `neutral` | 24.8 | 24 | 265,791 | 154,880 | 1,188 |
| `gpt-6-astra` | `no_code` | 24.6 | 24 | 265,863 | 126,720 | 1,241 |
| `gpt-6-astra` | `code_preferred` | 34.1 | 23 | 524,334 | 354,560 | 2,418 |

## Interpretation and next test

The supported finding is narrow: **under this shared custom prompt and these public reasoning questions, neither model spontaneously used visible code; both followed an explicit request to use it**. The study provides no positive evidence for the proposed Astra increase in this setting.

It cannot settle whether Astra writes more code in ordinary work. The questions are few, only four families are covered, accuracy is near ceiling, public-data familiarity cannot be excluded, each cell has one generation, and model-dependent developer context remains. It does not test file editing, artifact generation, browser tasks, unsolicited files, or the necessity and usefulness of code. A neutral arm with no events has limited sensitivity to the original observation.

A useful next preregistered replication would cross both models with public, versioned base prompts, including a default-like coding-assistant prompt, and a broader/harder standard-dataset sample. An API-native version should hold instructions, tool schemas and budgets fixed and use pinned model snapshots where available. Independent blinded trace labels and a paired-design power calculation should precede any claim about model weights or equivalence. This replication has not been run.

## Reproduce and data boundary

From the repository root:

```bash
python3 -m unittest discover -s tests -v
python3 studies/standard-benchmarks/verify.py
python3 studies/standard-benchmarks/reproduce.py --check
```

The verifier checks every planned cell, source/model identity, recorded model/configuration metadata for usable trials, scores, automatic code labels, paired analysis, audit consistency and byte checksums. Offline reanalysis does not call a model. To compare sampled questions with full pinned source files, follow the cache instructions in [the study card](README.md). A new run uses local Codex authentication and is a new stochastic experiment, not guaranteed to reproduce identical answers.

No personal conversation history or previous synthetic-study results are used in this analysis. Only this experiment's new trial logs were inspected. Published fields exclude raw host instruction bodies, credentials, session IDs and machine-local paths. Original session storage remains private. Prior-study working-tree files were deleted; **old public Git history still awaits separate confirmation for repository deletion and recreation**. We do not claim those historical copies are already erased.
