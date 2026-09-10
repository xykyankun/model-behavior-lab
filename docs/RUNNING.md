# Running trusted synthetic trials

The analysis commands run offline with Python 3.9+. The CLI runner supports POSIX
and was smoke-tested with Codex CLI 0.153.4 on macOS. No other CLI version is
claimed compatible. A missing flag or changed log schema must produce a failed
or invalid record, never an inferred “no code” result.

1. Install and log into Codex through its normal supported flow. Check `codex --version`.
2. Review every task, fixture and model in the specification. Use disposable data.
3. Seal a plan, record its hash in a commit before research collection, and choose a neutral output path outside your real project.
4. Run one infrastructure trial. Verify the answer, `valid`, requested/observed model, base/developer hashes, completion markers and sandbox.
5. Run the remaining planned attempts with a fixed stopping rule. Retain failures. Do not silently retry or relabel them as zeros.
6. Independently inspect full local logs for unexpected instructions, tool failures, scope changes and privacy before producing any public export.

```bash
python3 -m behavior_lab plan studies/code-propensity-2026-09/replication-spec.json private-runs/plan.json
python3 -m behavior_lab run private-runs/plan.json private-runs/results --max-runs 1
# Continue up to 47 not-yet-attempted trials, after the infrastructure check:
python3 -m behavior_lab run private-runs/plan.json private-runs/results --max-runs 47
python3 -m behavior_lab analyze private-runs/results --condition default --models gpt-5.6-sol gpt-6-astra
```

The plan embeds all fixtures, model identifiers, conditions and order. File names
cannot traverse outside the workspace or create hidden configurations. The runner
refuses a changed plan hash, duplicate output root, concurrent runner or incomplete
attempt directory. A crash may leave `runner.lock`; verify that its PID is no
longer running and document the incomplete attempt before removing that lock.

Analyzing a runner directory verifies each result against its saved plan and
includes unattempted jobs as missing. Analyzing a standalone JSON array cannot
discover entirely absent planned pairs; its completeness must be audited separately.

Trials run sequentially. `--max-runs` limits new attempts per invocation, not tokens
or money. Timeouts terminate the child process group; they do not guarantee a
remote inference request was cancelled. Stop at an account limit and report the
incomplete study. The runner does not buy credits, reset limits or alter default models.

Logs in `private-runs/` are git-ignored, but ignoring is not access control. Outputs
include raw synthetic tool inputs and private host metadata. Do not commit them
wholesale. There is no automatic public-export command: the included study was
allowlisted and reviewed separately. Full raw rollout files remain in Codex's own
session storage; the runner only resolves its exact trial thread via the read-only
state database. It never scans unrelated conversations.

The default child policy is `workspace-write`. Run untrusted agents/data in a
dedicated container or VM with credentials and host data isolated. This adapter is
not a general sandbox implementation, and host-readable data may be accessible.
Only use `--externally-sandboxed` when a parent already enforces equivalent
isolation. It selects `danger-full-access` for the child to avoid installing a
second sandbox; used without that parent it removes protection. Never use it as
an automatic fallback when the sandbox fails.

For TLS trust failures, repair the trusted CA configuration or point `SSL_CERT_FILE`
to a verified organizational/system CA bundle. Do not disable certificate verification.
The runner inherits normal authentication and network configuration but does not
record the environment or extract credentials.

Setting ignore flags does **not** guarantee that global instructions, host skills
or model-specific tool descriptions disappear. Inspect actual context hashes and
local traces. API-native equal-input experiments and Inspect adapters are future work.
