"""Paired, equal-task-weighted descriptive inference. No external dependencies."""

import itertools
import math
import random
from collections import defaultdict


def paired_summary(rows, model_a, model_b, metric="aux_code_with_awk", draws=20000, seed=1729):
    """Average repetitions within tasks, then compare matched tasks.

    Missing/invalid repeats cause the entire task pair to be excluded; a missing
    observation is never a negative. Call separately for each condition.
    Intervals assume exchangeable sampled tasks, which convenience sets lack.
    """
    if draws < 100:
        raise ValueError("At least 100 bootstrap draws required")
    cells = defaultdict(dict)
    seen = set()
    conditions = set()
    for row in rows:
        if row["model"] not in (model_a, model_b):
            continue
        conditions.add(row["condition"])
        key = (row["case"], row["model"], row["repeat"])
        if key in seen:
            raise ValueError("Duplicate task/model/repeat")
        seen.add(key)
        value = row.get(metric)
        if value is not None and type(value) is not bool:
            raise ValueError("Binary metrics must be bool or null")
        cells[(row["case"], row["model"])][row["repeat"]] = (
            value if row.get("valid") is True else None
        )
    if len(conditions) != 1:
        raise ValueError("Analyze exactly one condition at a time")
    matched, excluded = [], []
    for case in sorted({key[0] for key in cells}):
        a, b = cells[(case, model_a)], cells[(case, model_b)]
        if not a or set(a) != set(b) or None in a.values() or None in b.values():
            excluded.append(case)
            continue
        ma, mb = sum(a.values()) / len(a), sum(b.values()) / len(b)
        matched.append({"case": case, "a": ma, "b": mb, "difference": mb - ma})
    if not matched:
        raise ValueError("No complete matched tasks")
    diffs = [r["difference"] for r in matched]
    n = len(diffs)
    effect = sum(diffs) / n
    rng = random.Random(seed)
    boot = sorted(sum(rng.choices(diffs, k=n)) / n for _ in range(draws))
    nonzero = [d for d in diffs if d != 0]
    observed = abs(sum(diffs))
    if len(nonzero) <= 20:
        null = [abs(sum(s * d for s, d in zip(signs, nonzero)))
                for signs in itertools.product((-1, 1), repeat=len(nonzero))]
        p = sum(v >= observed - 1e-12 for v in null) / len(null)
        method = "exact task-level sign-flip"
    else:
        count = sum(abs(sum(rng.choice((-1, 1)) * d for d in nonzero))
                    >= observed - 1e-12 for _ in range(draws))
        p = (count + 1) / (draws + 1)
        method = "Monte Carlo task-level sign-flip (+1 correction)"
    return {
        "metric": metric, "model_a": model_a, "model_b": model_b,
        "matched_tasks": n, "excluded_tasks": excluded, "task_means": matched,
        "a_mean": sum(r["a"] for r in matched) / n,
        "b_mean": sum(r["b"] for r in matched) / n,
        "difference_b_minus_a": effect,
        "bootstrap_percentile_95": [boot[int(.025 * draws)], boot[int(.975 * draws) - 1]],
        "sign_flip_p_two_sided": p, "test": method, "seed": seed, "draws": draws,
        "interpretation": "Exploratory; assumes exchangeable tasks and symmetric differences under null. Not a causal test or a population CI for a hand-picked set. No multiplicity correction.",
    }


def planning_sample_size(p_a=.2, p_b=.35):
    """Normal approximation: two independent proportions, alpha=.05, power=.8.

    Planning illustration only; a paired/clustered design requires its own
    correlation assumptions or simulation, not substitution of repeated runs.
    """
    if not (0 < p_a < 1 and 0 < p_b < 1) or p_a == p_b:
        raise ValueError("Distinct probabilities strictly between zero and one required")
    p = (p_a + p_b) / 2
    return math.ceil(((1.95996398454 * math.sqrt(2 * p * (1 - p)) +
                       .84162123357 * math.sqrt(p_a * (1 - p_a) + p_b * (1 - p_b)))
                      / (p_b - p_a)) ** 2)
