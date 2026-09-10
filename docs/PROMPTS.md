# Prompt analysis and intervention

The experiment separates two questions: what a model chooses under a neutral
request, and how its behavior changes when a request explicitly constrains the
method. The second does not by itself explain the first.

## Fixed components

The shared base instruction is defined in `behavior_lab/benchmarks.py`:

> You are an assistant solving the user's question. Follow the requested method and answer format. Work only on the supplied question. Do not browse the web or inspect files outside the current workspace.

The upstream question is preserved verbatim. A common final-answer instruction
is appended, followed by one of three method instructions. The numeric, word-list
or multiple-choice format depends on the task, and is identical across conditions
for the same question. No reference answer is inserted into the model prompt or
workspace. Reference answers are kept in the runner's plan outside the workspace.
This is not a hardened defense against an agent reading parent directories: use
an isolated evaluation service for adversarial settings.

| Condition | Method instruction | Expected manipulation |
|---|---|---|
| Neutral | Choose the method you consider appropriate. | Allows either direct reasoning or a program |
| No code | Solve without writing or executing any task-specific program. | Tests obedience to a method constraint |
| Code preferred | Write and execute a short program to solve or verify the answer. | Tests whether the model can and will use code |

We do not request hidden chain-of-thought. The final line must be `FINAL: <answer>`.
A malformed final answer counts as an output-format failure and an incorrect
answer, not a missing observation. Infrastructure failures remain missing.

## What can be estimated

Within each model, compare code-candidate rates and correctness on the same
questions under each prompt. Report both the neutral model difference and the
model-by-prompt interaction:

`interaction = (B_code_preferred - B_neutral) - (A_code_preferred - A_neutral)`

An analogous contrast applies to the no-code arm. Average repetitions within each
question before analysis; report each dataset separately as well as any declared
aggregate. Do not pool a model's neutral arm with its forced-code positive control.

A model that uses code only when requested is different from one that uses it
spontaneously. A drop in accuracy under no-code instructions might indicate a
useful tool dependency, but requires adequate independent questions and reliable
scoring. An increased code rate under the code-preferred prompt is an instruction
response, not proof that the model naturally prefers coding.

## What remains uncontrolled

The shared base is only one part of a Codex request. Host developer instructions,
tool descriptions, model routing and server-side behavior may differ. The runner
records effective base/developer hashes and requested/observed model IDs from the
actual trial. Equal CLI flags are not proof of equal requests or fixed weights. The model IDs
come from CLI context records, not independent backend weight attestation.
No personal conversation history is used as a dataset or evidence source.

To identify a model-weight effect, use a separate API-native replication with
identical visible instructions, tools, history and budgets, plus fixed model
snapshots where available. That adapter is not implemented here. A useful second
ablation would cross public, versioned base prompts with both models; do not
infer the contribution of each prompt component from one opaque product setup.

[OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
supports task-specific evaluation and calibrated scoring. The
[PAL paper](https://arxiv.org/abs/2211.10435) studies program-aided problem solving;
it motivates measuring correctness alongside method choice, not treating code use
as a failure. Neither source establishes a GPT-6-versus-GPT-5.6 behavior difference.
