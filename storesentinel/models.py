"""Core data models: Rule, Finding, ScanResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

SEVERITY_ERROR = "error"
SEVERITY_WARN = "warn"
SEVERITY_INFO = "info"

SEVERITY_WEIGHT = {SEVERITY_ERROR: 10, SEVERITY_WARN: 3, SEVERITY_INFO: 0}


@dataclass(frozen=True)
class Rule:
    """A single rejection-risk rule definition."""

    rule_id: str
    severity: str  # error | warn | info
    title: str
    description: str
    fix_hint: str
    platform: str  # ios | android | flutter | rn | general

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "fix_hint": self.fix_hint,
            "platform": self.platform,
        }


@dataclass
class Finding:
    """One concrete issue detected in the scanned project."""

    rule: Rule
    message: str
    file_path: str = ""
    line: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "rule_id": self.rule.rule_id,
            "severity": self.rule.severity,
            "platform": self.rule.platform,
            "title": self.rule.title,
            "message": self.message,
            "file": self.file_path,
            "line": self.line,
            "fix_hint": self.rule.fix_hint,
        }


@dataclass
class ScanResult:
    """Aggregated result of one scan run."""

    project_path: str
    findings: list = field(default_factory=list)
    platforms_detected: list = field(default_factory=list)
    rules_total: int = 0

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.rule.severity == SEVERITY_ERROR)

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.rule.severity == SEVERITY_WARN)

    @property
    def infos(self) -> int:
        return sum(1 for f in self.findings if f.rule.severity == SEVERITY_INFO)

    @property
    def score(self) -> int:
        """0-100 readiness score. 100 = no findings at all."""
        penalty = sum(
            SEVERITY_WEIGHT.get(f.rule.severity, 0) for f in self.findings
        )
        return max(0, 100 - penalty)

    def as_dict(self) -> dict:
        return {
            "project": self.project_path,
            "platforms": self.platforms_detected,
            "score": self.score,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "rules_total": self.rules_total,
            "findings": [f.as_dict() for f in self.findings],
        }
