# Methodology

## Constructs and evidence

Separate auxiliary programming, language choice, tool use, unrequested artifacts,
and task quality. A tool wrapper is not necessarily task logic; Python, awk,
JavaScript and shell programs can serve the same purpose. The automatic detector
currently recognizes inline Python/Node/Ruby/Perl and awk candidates. It can miss
standalone generated scripts, shell logic, SQL and in-memory JavaScript, and can
match quoted command text. Its name and version must retain that limitation.

Use independent, blinded annotation before claiming a complete measure of
programming or unnecessary work. Recommended labels are program authored,
execution attempted/succeeded, language, purpose, scope compliance, necessity and
correctness. Calibrate two annotators on examples, report agreement and disputes,
and validate any model judge against independent labels.

## Dataset selection

Use only public, licensed benchmark sources with pinned commits, byte checksums,
source indices and preserved license notices. GSM8K is drawn from its test split;
BBH uses its published evaluation examples. The selected BBH tasks cover sorting,
counting and relational reasoning. They do not represent all non-coding work.
Code-generation datasets would be positive controls rather than suitable primary
data for measuring unsolicited code use.

Sampling uses a fixed seed within each source, independently of model outputs.
The seed controls question selection and run order only; the CLI adapter does not
set a generation seed or temperature. One attempt per cell does not characterize
within-question sampling variability.
Questions are copied verbatim; method and final-answer instructions are explicit
adaptations. Tool access and zero-shot prompting make this a dataset-backed
behavior study, not a reproduction of a published leaderboard protocol. Benchmark
familiarity or contamination may reduce sensitivity; harder, independently held-out
public tasks are needed for broader claims.

## Experimental design

Cross model identity with neutral, no-code and code-preferred prompts on matched
questions. Keep the base instruction, question, format and reasoning setting
fixed. Randomize trial order and use a fresh, opaque workspace for each attempt.
Record the exact prompt specification and effective context hashes. Treat the
Codex model-plus-configuration as the treatment when complete request equality
cannot be demonstrated. See [PROMPTS.md](PROMPTS.md).

Freeze the protocol before collecting results and publish its commit/hash.
A local seal prevents accidental changes but is not independent proof of when
an experiment was registered. Report the total scheduled, attempted, completed,
invalid and unattempted cells. Never retain only successful or favorable runs.

## Scoring and dependence

Numeric answers use normalized decimal equality, choices use their exact option
labels, and sorted words use exact sequence equality. Every valid attempt is
scored separately for format compliance and correctness. A malformed answer is
incorrect; failed or incomplete infrastructure is missing. Reference answers are
not model-visible task inputs. Public reference answers can contain errors, so
any disputed item needs a documented adjudication rather than silent relabeling.

The analysis first averages repetitions within each question, then averages the
paired model differences across questions. It bootstraps complete question pairs
and performs a task-level sign-flip sensitivity test. Missing/invalid repeats
exclude the entire question pair and are listed. A runner-directory analysis
includes all scheduled jobs; an arbitrary JSON array cannot reveal omitted pairs.

Do not confuse questions with independent task families. Analyze each dataset
separately; any cross-dataset aggregate must specify its weights. The supplied analysis assigns equal weight
to each question, so a full-corpus aggregate gives more weight to GSM8K. Equal
sampling per source gives equal source weights before exclusions. Complete-case
exclusions can change the realized source weights; report the retained questions
and source counts rather than claiming that balance is preserved. The statistics
assume exchangeability of sampled questions, and the sign-flip test assumes
symmetric difference signs under the null. Small pilots and few discordant pairs
produce weak inference. No multiplicity correction is currently implemented;
multiple prompts, metrics and subgroup analyses must be labeled exploratory.

When every observed paired difference is zero, the empirical bootstrap returns
the degenerate interval `[0, 0]`. That result does not establish equivalence or
exclude meaningful population differences. The published study also reports
[Wilson intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
for marginal proportions, with their binomial assumptions stated. Worst-case
missing-data bounds assign every unusable planned observation either zero or one;
they describe the fixed planned sample, not population sampling uncertainty.

Define a minimum meaningful effect and plan sample size using the paired design,
question-family dependence and expected failure rate. Repeated runs of one easy
question do not replace independent questions. A 24-attempt pilot with four unique
questions is for infrastructure and manipulation checks, not a model ranking.

## Related methods

- [GSM8K / Training Verifiers](https://arxiv.org/abs/2110.14168): arithmetic questions with reference solutions; use the published test split.
- [BIG-Bench Hard](https://arxiv.org/abs/2210.09261): a collection of challenging reasoning tasks; its original prompting protocol differs from this adaptation.
- [PAL](https://arxiv.org/abs/2211.10435): program-aided reasoning motivates assessing code use and correctness together.
- [HELM](https://arxiv.org/abs/2211.09110): standardized scenarios and multiple metrics motivate explicit coverage and trade-offs.
- [Construct validity](https://arxiv.org/abs/2511.04703): motivates distinguishing lexical code candidates from the broader behavioral construct.
- [Statistical significance in NLP](https://aclanthology.org/P18-1128/): motivates choosing a test around the actual design and measurement.
- [AI Agents That Matter](https://arxiv.org/abs/2407.01502): motivates tracking costs, holdouts and reproducibility alongside accuracy.

These sources guide the design; they are not evidence for the target model comparison.
