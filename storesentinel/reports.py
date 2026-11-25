"""Report renderers: text (ANSI), JSON, SARIF."""

from __future__ import annotations

import json
import sys
from . import __version__
from .models import ScanResult

_SEV_ORDER = {"error": 0, "warn": 1, "info": 2}

ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "grey": "\033[90m",
    "green": "\033[32m",
}


def _c(enabled: bool, key: str, text: str) -> str:
    if not enabled:
        return text
    return ANSI[key] + text + ANSI["reset"]


def render_text(result: ScanResult, color: bool = True) -> str:
    """Human-readable console report."""
    lines = []
    name = result.project_path
    lines.append(_c(color, "bold", "StoreSentinel scan report"))
    lines.append(_c(color, "grey", f"Project : {name}"))
    plats = ", ".join(result.platforms_detected) or "none"
    lines.append(_c(color, "grey", f"Platforms: {plats}"))

    score = result.score
    badge = "red" if score < 60 else ("yellow" if score < 90 else "green")
    lines.append(_c(color, badge,
                    f"Readiness score: {score}/100  "
                    f"({result.errors} errors, {result.warnings} warnings, "
                    f"{result.infos} infos)"))
    lines.append("")

    if not result.findings:
        lines.append(_c(color, "green", "No rejection risks detected. 🎉"))
        return "\n".join(lines)

    last_sev = None
    for f in result.findings:
        sev = f.rule.severity
        if sev != last_sev:
            sev_label = {"error": "ERRORS", "warn": "WARNINGS",
                         "info": "INFO"}[sev]
            key = {"error": "red", "warn": "yellow", "info": "cyan"}[sev]
            lines.append(_c(color, "bold", f"-- {sev_label} " + "-" * 40))
            last_sev = sev
        loc = f.file_path or "-"
        if f.line:
            loc += f":{f.line}"
        lines.append(f"[{f.rule.rule_id}] {f.message}")
        lines.append(_c(color, "grey", f"    file: {loc}"))
        lines.append(_c(color, "grey", f"    fix : {f.rule.fix_hint}"))
    lines.append("")
    lines.append(f"Rules evaluated: {result.rules_total}")
    return "\n".join(lines)


def render_json(result: ScanResult) -> str:
    return json.dumps(result.as_dict(), indent=2, ensure_ascii=False)


def render_sarif(result: ScanResult) -> str:
    """Render findings as SARIF 2.1.0 (GitHub code scanning compatible)."""
    rules = []
    seen = set()
    for f in result.findings:
        if f.rule.rule_id in seen:
            continue
        seen.add(f.rule.rule_id)
        rules.append({
            "id": f.rule.rule_id,
            "shortDescription": {"text": f.rule.title},
            "fullDescription": {"text": f.rule.description},
            "help": {"text": f.rule.fix_hint},
            "defaultConfiguration": {"level": _sarif_level(f.rule.severity)},
            "properties": {"platform": f.rule.platform},
        })

    results = []
    for f in result.findings:
        art = {"uri": f.file_path or "."}
        region = {"startLine": max(1, f.line or 1)}
        results.append({
            "ruleId": f.rule.rule_id,
            "level": _sarif_level(f.rule.severity),
            "message": {"text": f.message},
            "locations": [{"physicalLocation": {
                "artifactLocation": art,
                "region": region,
            }}],
        })

    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "StoreSentinel",
                "version": __version__,
                "informationUri": "https://github.com/gitstq/StoreSentinel",
                "rules": rules,
            }},
            "results": results,
        }],
    }
    return json.dumps(sarif, indent=2, ensure_ascii=False)


def _sarif_level(sev: str) -> str:
    return {"error": "error", "warn": "warning", "info": "note"}.get(
        sev, "note")


def write_report(result: ScanResult, fmt: str, out_path: str = None,
                 color: bool = True) -> None:
    """Render the result in *fmt* and write to out_path or stdout."""
    if fmt == "json":
        text = render_json(result)
    elif fmt == "sarif":
        text = render_sarif(result)
    else:
        text = render_text(result, color=color)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
