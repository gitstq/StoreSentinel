"""Rule registry: all built-in rules in one place."""

from __future__ import annotations

from .models import Rule

# Imported for side-effect registration only.
from .scanners.ios import (RULE_ENCRYPTION, RULE_PRIVACY_MANIFEST, RULE_ATS,
                           RULE_LAUNCH, RULE_PURPOSE)
from .scanners.android import (RULE_DEBUGGABLE, RULE_CLEARTEXT,
                               RULE_DANGEROUS, RULE_TARGET_SDK,
                               RULE_EXPORTED, RULE_PACKAGE_NAME,
                               RULE_VERSION)
from .scanners.flutter import RULE_FLT_VERSION, RULE_FLT_DESC
from .scanners.general import RULE_PRIVACY_DOC

ALL_RULES = [
    RULE_ENCRYPTION, RULE_PRIVACY_MANIFEST, RULE_ATS, RULE_LAUNCH,
    RULE_PURPOSE,
    RULE_DEBUGGABLE, RULE_CLEARTEXT, RULE_DANGEROUS, RULE_TARGET_SDK,
    RULE_EXPORTED, RULE_PACKAGE_NAME, RULE_VERSION,
    RULE_FLT_VERSION, RULE_FLT_DESC,
    RULE_PRIVACY_DOC,
]

RULES_BY_ID = {r.rule_id: r for r in ALL_RULES}
