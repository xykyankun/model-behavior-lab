"""Versioned lexical proxies, NOT a semantic detector of all programming."""

import re

METRIC_VERSION = "legacy-2026-09-10"
SCRIPT = re.compile(
    r'(?:python[\d.]*|node|ruby|perl)\s+(?:-c\b|-e\b|-p\b|--eval\b|--print\b|-\s*<<)'
    r'|python[\d.]*\s+<<'
    r'|\b(?:python[\d.]*|node)\b[^\n]{0,100}<<'
    r'|\bnode\s+--input-type(?:=|\s+)(?:module|commonjs)\s+(?:-e\b|-p\b|--eval\b|--print\b)'
    r'|\b(?:perl|ruby)\s+(?:-[A-Za-z0-9]+\s+)*-[A-Za-z0-9]*e\b'
)
AWK = re.compile(r'\b(?:gawk|mawk|awk)\s')


def candidates(calls):
    # Keep this historical definition stable so the published study recomputes.
    # Text in quoted documentation can be a false positive. No candidate is
    # automatically interpreted as unnecessary work or successful execution.
    body = "\n".join(str(x.get("body", "")) for x in calls)
    narrow = bool(SCRIPT.search(body))
    return {"inline_script": narrow, "awk_code": bool(AWK.search(body)),
            "aux_code_with_awk": narrow or bool(AWK.search(body))}
