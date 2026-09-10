# Contributing a behavior experiment

Start with a falsifiable question, such as “Does a model ask fewer clarifying
questions under ambiguous requirements?” or “Does verification code improve
correctness on small file edits?” Specify the target population and the smallest
difference that would matter to a user.

Include:

1. A protocol and pre-collection commit/hash, primary metric, controls and stopping rule.
2. Public, explicitly licensed benchmark prompts and held-out task families.
3. Model/configuration/tool provenance and known inputs you could not equalize.
4. All attempts and failures; no selected successes or hidden post-hoc task changes.
5. A reproducible analysis with task-level dependence and uncertainty addressed.
6. Counterexamples, quality trade-offs, missing evidence and limitations.
7. An allowlisted public dataset and privacy review. Never contribute personal transcripts or credentials.

Keep observational evidence, exploratory experiments and confirmatory studies
separate. A local timestamp is not an independent preregistration. New metrics
need versioned definitions and examples of positives, negatives and ambiguous
cases. Preserve old labels when correcting them, with an explanation of what changed.

Run `python3 -m unittest discover -s tests -v` and
`python3 studies/standard-benchmarks/verify.py` before proposing a change.
Tests must not make paid model calls or execute contributed model-generated code
on the CI host. New execution adapters should reuse mature sandbox infrastructure.

Pull requests are welcome for replication results, detector mistakes, null
findings, statistical corrections and improved task coverage. Do not change a
study's conclusion just to make a model look better or worse.
