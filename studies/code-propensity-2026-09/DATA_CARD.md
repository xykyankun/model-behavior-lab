# Data card

- **Purpose:** exploratory comparison of auxiliary-program candidates in one Codex setup.
- **Population:** synthetic Chinese prompts chosen by one investigator, plus private historical turns from one consenting user. Not representative of all tasks or languages.
- **Models:** `gpt-5.6-sol`, `gpt-6-astra`; mutable CLI identifiers, no independently verified weight snapshot.
- **Published:** 16 original cases, 84 synthetic final answers and tool-call inputs, two original local protocols, derived metrics, validation summary, context hashes, historical aggregates and a future protocol.
- **Not published:** private historical prompts, private project code, conversation identifiers, tool outputs, host system/developer instruction bodies, auth files, certificates or original home paths.
- **Transform:** explicit field allowlist for synthetic trials; home/workspace paths and session IDs replaced. Public trial IDs renumbered; original randomized ordering remains in protocol files. No answer wording otherwise intentionally changed.
- **Label provenance:** legacy lexical detector plus auditing by the investigating assistant. No independent human gold labels, precision/recall estimate or inter-rater reliability. `valid` means the original audit accepted a complete trial; it is not a correctness score.
- **Potential leakage:** original task paths included model and condition names. Host instructions remained. Data has been observed during framework development and cannot now be a clean hidden test set.
- **Dependence:** repeated trials share task families and runtime infrastructure; historical turns share conversations. Effective evidence is not 84 independent task types or 1,633 independent users.
- **Missingness:** all 84 formal trials valid in original audit; 29 completed pilots excluded, 31 pilot jobs cancelled. Future experiments must report all planned attempts, including missing telemetry.
- **Quality:** numeric/file/function checks were performed during original collection. `validation-legacy.json` records those checks. Offline reproduction recomputes proxies and statistics, not the original execution outcomes or a complete quality benchmark.
- **License:** repository-authored code, prompts, fixtures and documentation under MIT. Generated outputs are included as research evidence; no claim is made to ownership of third-party material a model may reproduce.
- **Integrity:** `checksums.json` covers published JSON files except itself. Hashes establish internal consistency, not independent origin or untampered collection.

`analysis.json` is derived by `reproduce.py`. `trials.json` contains one row per
synthetic trial, including case/model/condition/repeat, candidate booleans, usage,
latency, answer and calls. `inline_script` is the narrower interpreter proxy;
`aux_code_with_awk` adds awk. Use the latter for the headline comparison.
`history-aggregates.json` cannot be independently reconstructed without the private corpus.

The historical base-hash algorithm differs from the new runner's compact canonical
JSON hash. See `provenance.json`; do not compare those two hash encodings directly.
