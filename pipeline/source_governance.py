"""
pipeline/source_governance.py — Source governance and compliance automation.

Implements the source layer of the 4-layer architecture:
  Source → Generation → Verification → Publishing

Key responsibilities:
1. Source allowlist management (CC/OER/public-domain only)
2. License decision automation (allow/deny/needs_review)
3. Evidence preservation (URL + license_type + timestamp + snapshot)
4. Content similarity detection for anti-textbook-reproduction
5. Priority source ranking

References:
- 教育大市集 (CC, TW LOM, API)
- 課綱原文 (行政院公報資訊網 107 年版)
- 素養導向紙筆測驗範例 (教育部)
- 著作權聲明公共領域規則
- 國家教育研究院教師手冊 (結構性資訊)
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

# ── Source Allowlist ────────────────────────────────────────

# Priority-ordered source domains (official/OER first)
SOURCE_PRIORITY = [
    {
        "domain": "gazette.nat.gov.tw",
        "name": "行政院公報資訊網（課綱原文）",
        "license_default": "public-domain",
        "priority": 1,
        "notes": "第三學習階段能力敘述、學習表現編碼、分年學習內容條目",
    },
    {
        "domain": "market.cloud.edu.tw",
        "name": "教育大市集（教育雲 OER）",
        "license_default": "CC BY-NC-SA 4.0",
        "priority": 2,
        "notes": "CC 授權、TW LOM 後設資料、API 介接",
    },
    {
        "domain": "www.naer.edu.tw",
        "name": "國家教育研究院",
        "license_default": "needs_review",
        "priority": 3,
        "notes": "結構性資訊可用，不重製內容",
    },
    {
        "domain": "www.edu.tw",
        "name": "教育部（素養測驗範例）",
        "license_default": "public-domain",
        "priority": 4,
        "notes": "素養導向紙筆測驗要素與範例試題",
    },
    {
        "domain": "gpi.culture.tw",
        "name": "政府出版品資訊網",
        "license_default": "needs_review",
        "priority": 5,
        "notes": "教師手冊結構性資訊，須完成授權評估",
    },
]

DOMAIN_ALLOWLIST = {s["domain"] for s in SOURCE_PRIORITY}

LICENSE_ALLOWLIST = frozenset({
    "CC BY 4.0",
    "CC BY-SA 4.0",
    "CC BY-NC 4.0",
    "CC BY-NC-SA 4.0",
    "CC BY 3.0",
    "CC BY-SA 3.0",
    "CC BY-NC 3.0",
    "CC BY-NC-SA 3.0",
    "CC0",
    "CC0 1.0",
    "public-domain",
})

LICENSE_DENY = frozenset({
    "all-rights-reserved",
    "unknown",
    "proprietary",
})

# ── License Decision Engine ────────────────────────────────

def decide_license(license_type: str, url: str = "") -> str:
    """
    Automated license decision: allow / deny / needs_review.

    Rules:
    1. If license_type is in LICENSE_ALLOWLIST → allow
    2. If license_type is in LICENSE_DENY → deny
    3. If URL domain is in DOMAIN_ALLOWLIST and license not explicitly denied → needs_review
    4. Otherwise → needs_review
    """
    lt = license_type.strip()
    if lt in LICENSE_ALLOWLIST:
        return "allow"
    if lt in LICENSE_DENY:
        return "deny"
    return "needs_review"


def validate_source(source: dict) -> tuple[bool, str]:
    """
    Validate source metadata completeness and compliance.

    Returns (ok, reason).
    """
    required = ["url", "license_type", "captured_at"]
    for f in required:
        if f not in source or not source[f]:
            return False, f"source missing required field: {f}"

    lt = source["license_type"]
    decision = source.get("license_decision", "needs_review")

    # Hard deny
    if lt in LICENSE_DENY:
        return False, f"license '{lt}' is in deny list — cannot auto-publish"
    if decision == "deny":
        return False, "license_decision is 'deny' — blocked"

    # Must be on allowlist for auto-publish
    if lt not in LICENSE_ALLOWLIST and decision != "allow":
        return False, (
            f"license '{lt}' not on allowlist; "
            f"decision='{decision}' — needs manual review"
        )

    return True, "ok"


# ── Content Similarity ─────────────────────────────────────

def text_similarity(a: str, b: str) -> float:
    """
    Compute text similarity ratio (0.0–1.0) using SequenceMatcher.
    Used for anti-textbook-reproduction and dedup checks.
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def check_similarity_against_bank(
    question: str,
    existing_questions: list[str],
    threshold: float = 0.85,
) -> tuple[bool, float, int | None]:
    """
    Check if a question is too similar to existing ones.

    Returns (is_unique, max_similarity, most_similar_index_or_None).
    """
    max_sim = 0.0
    max_idx = None
    for i, eq in enumerate(existing_questions):
        sim = text_similarity(question, eq)
        if sim > max_sim:
            max_sim = sim
            max_idx = i
    is_unique = max_sim < threshold
    return is_unique, max_sim, max_idx if max_sim >= threshold else None


# ── Evidence Preservation ──────────────────────────────────

def create_evidence_hash(content: str) -> str:
    """Create SHA-256 hash of content for snapshot evidence."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_source_metadata(
    url: str,
    license_type: str,
    content_snapshot: str = "",
) -> dict:
    """
    Build a complete source metadata dict with auto-populated fields.
    """
    now = datetime.now(timezone.utc).isoformat()
    decision = decide_license(license_type, url)
    meta = {
        "url": url,
        "license_type": license_type,
        "captured_at": now,
        "license_decision": decision,
    }
    if content_snapshot:
        meta["evidence_snapshot"] = create_evidence_hash(content_snapshot)
    return meta


# ── Textbook Reproduction Detection ────────────────────────

# Patterns suggesting direct textbook reproduction
TEXTBOOK_PATTERNS = [
    r"第\s*\d+\s*課",          # 第X課 (chapter markers)
    r"課本\s*第\s*\d+\s*頁",   # 課本第X頁
    r"習作\s*第?\s*\d+",       # 習作第X
    r"翰林|南一|康軒",          # Major textbook publishers
    r"教科書",                  # Textbook reference
    r"出版社",                  # Publisher reference
]
TEXTBOOK_RE = re.compile("|".join(TEXTBOOK_PATTERNS), re.IGNORECASE)


def check_textbook_reproduction(text: str) -> tuple[bool, str | None]:
    """
    Check if text contains patterns suggesting direct textbook reproduction.
    Returns (is_safe, matched_pattern_or_None).
    """
    match = TEXTBOOK_RE.search(text)
    if match:
        return False, match.group()
    return True, None
