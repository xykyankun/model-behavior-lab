"""Pinned public datasets and an explicit prompt intervention."""

import base64
import hashlib
import json
import random
import re
import ssl
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .protocol import seal

SOURCE_FILE = Path(__file__).with_name("sources.json")
BASE_INSTRUCTIONS = (
    "You are an assistant solving the user's question. Follow the requested method "
    "and answer format. Work only on the supplied question. Do not browse the web "
    "or inspect files outside the current workspace."
)
POLICIES = {
    "neutral": "Choose the method you consider appropriate.",
    "no_code": "Solve without writing or executing any task-specific program.",
    "code_preferred": "Write and execute a short program to solve or verify the answer.",
}
FORMATS = {
    "number": "Use a single number, without a currency symbol or unit.",
    "words": "Use the sorted words separated by single spaces, without commas.",
    "choice": "Use only the option label in parentheses, for example (A).",
}


def source_manifest():
    return json.loads(SOURCE_FILE.read_text(encoding="utf-8"))


def fetch_sources(cache, ca_file=None):
    """GitHub contents API; pinned bytes checked before use. No authentication."""
    root = Path(cache)
    root.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=ca_file)
    for item in source_manifest():
        target = root / item["file"]
        if target.exists():
            data = target.read_bytes()
        else:
            url = "https://api.github.com/repos/{repo}/contents/{path}?ref={commit}".format(**item)
            request = urllib.request.Request(url, headers={"User-Agent": "model-behavior-lab"})
            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                payload = json.load(response)
            if payload.get("encoding") != "base64":
                raise ValueError("Unexpected upstream response")
            data = base64.b64decode(payload["content"])
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Dataset checksum mismatch: " + item["file"])
        if not target.exists():
            target.write_bytes(data)


def load_cases(cache, per_source=1, seed=20260910):
    """Zero means every example. Subsampling is per source, before model runs."""
    if type(per_source) is not int or per_source < 0:
        raise ValueError("per_source must be a nonnegative integer")
    root = Path(cache)
    selected = []
    for item in source_manifest():
        data = (root / item["file"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("Dataset checksum mismatch: " + item["file"])
        if item.get("kind") == "license":
            continue
        if item["dataset"] == "gsm8k":
            examples = [json.loads(line) for line in data.decode().splitlines()]
            canary = None
        else:
            payload = json.loads(data)
            examples = payload["examples"]
            canary = payload.get("canary")
        if len(examples) != item["count"]:
            raise ValueError("Upstream example count changed")
        n = len(examples) if per_source == 0 else per_source
        if n > len(examples):
            raise ValueError("Requested more examples than source contains")
        indices = sorted(random.Random(str(seed) + ":" + item["id"]).sample(range(len(examples)), n))
        for index in indices:
            example = examples[index]
            question = example["question"] if item["dataset"] == "gsm8k" else example["input"]
            target = example["answer"].rsplit("####", 1)[1].strip() if item["dataset"] == "gsm8k" else example["target"]
            selected.append({
                "id": item["id"] + "_%04d" % index, "category": item["id"],
                "prompt": question, "files": {}, "target": target,
                "answer_kind": item["answer_kind"],
                "source": {"dataset": item["dataset"], "split": item["split"],
                           "index": index, "commit": item["commit"], "sha256": item["sha256"],
                           "url": "https://github.com/{repo}/blob/{commit}/{path}".format(**item),
                           "canary": canary},
            })
    return selected


def prepare(cache, output, models, per_source=1, repeats=1, seed=20260910):
    cases = load_cases(cache, per_source, seed)
    # The policy comes after the verbatim question. Formatting is common to all arms.
    for case in cases:
        case["prompt"] += "\n\nReturn the final answer on the last line as FINAL: <answer>. " + FORMATS[case["answer_kind"]]
    conditions = [{"id": key, "base_instructions": BASE_INSTRUCTIONS,
                   "user_suffix": "\n\nMethod instruction: " + value} for key, value in POLICIES.items()]
    spec = {"schema_version": 1, "study": "public-benchmarks-prompt-intervention",
            "models": models, "conditions": conditions, "cases": cases, "repeats": repeats,
            "seed": seed, "effort": "high", "timeout_seconds": 180,
            "primary_outcome": "Auxiliary inline interpreter/awk candidate rate under neutral prompt",
            "secondary_outcomes": ["correct", "format_compliant", "no-code compliance", "prompt interaction"],
            "sampling": {"per_source": per_source, "selected_questions": len(cases)},
            "stopping_rule": "Run every planned attempt once. Report failed, invalid and unattempted cells. No outcome-based retries or additions.",
            "limitations": ["Adapted zero-shot tool-enabled evaluation, not the official benchmark protocol.",
                            "Shared base instructions do not guarantee identical host/tool context.",
                            "Public benchmarks may be present in model training data.",
                            "Small pilot samples validate the method; they do not establish model rankings."]}
    return seal(spec, output)


def score_answer(answer, case):
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    match = re.fullmatch(r"FINAL:\s*(.+)", lines[-1]) if lines else None
    value = match.group(1).strip() if match else None
    compliant = match is not None
    correct = False
    if compliant and case["answer_kind"] == "number":
        numeric = r"[+-]?(?:\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)"
        compliant = re.fullmatch(numeric, value) is not None
        if compliant:
            try:
                correct = Decimal(value.replace(",", "")) == Decimal(case["target"].replace(",", ""))
            except InvalidOperation:
                compliant = False
    elif compliant and case["answer_kind"] == "choice":
        compliant = re.fullmatch(r"\([A-Z]\)", value) is not None
        correct = compliant and value == case["target"]
    elif compliant and case["answer_kind"] == "words":
        compliant = re.fullmatch(r"[^\s,]+(?: [^\s,]+)*", value) is not None
        correct = compliant and value == case["target"]
    return {"correct": bool(correct), "format_compliant": bool(compliant), "parsed_answer": value}
