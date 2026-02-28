"""
tests/unit/test_pipeline_source_governance.py — Unit tests for source governance module.

Covers:
- License decision automation (allow/deny/needs_review)
- Source validation (required fields, deny/allowlist logic)
- Content similarity detection
- Textbook reproduction detection
- Evidence hash generation
- Source metadata building
"""
import pytest

from pipeline.source_governance import (
    LICENSE_ALLOWLIST,
    LICENSE_DENY,
    build_source_metadata,
    check_similarity_against_bank,
    check_textbook_reproduction,
    create_evidence_hash,
    decide_license,
    text_similarity,
    validate_source,
)


class TestDecideLicense:
    """License decision engine tests."""

    @pytest.mark.parametrize("lt", list(LICENSE_ALLOWLIST))
    def test_allowed_licenses(self, lt):
        assert decide_license(lt) == "allow"

    @pytest.mark.parametrize("lt", list(LICENSE_DENY))
    def test_denied_licenses(self, lt):
        assert decide_license(lt) == "deny"

    def test_unknown_license_needs_review(self):
        assert decide_license("custom-academic") == "needs_review"

    def test_whitespace_handling(self):
        assert decide_license("  CC BY 4.0  ") == "allow"


class TestValidateSource:
    """Source metadata validation tests."""

    def test_valid_source(self):
        src = {
            "url": "https://market.cloud.edu.tw/example",
            "license_type": "CC BY 4.0",
            "captured_at": "2026-01-01T00:00:00Z",
            "license_decision": "allow",
        }
        ok, msg = validate_source(src)
        assert ok is True

    @pytest.mark.parametrize("missing", ["url", "license_type", "captured_at"])
    def test_missing_required_field(self, missing):
        src = {
            "url": "https://example.com",
            "license_type": "CC BY 4.0",
            "captured_at": "2026-01-01T00:00:00Z",
        }
        del src[missing]
        ok, msg = validate_source(src)
        assert ok is False
        assert missing in msg

    def test_denied_license_fails(self):
        src = {
            "url": "https://example.com",
            "license_type": "all-rights-reserved",
            "captured_at": "2026-01-01T00:00:00Z",
        }
        ok, msg = validate_source(src)
        assert ok is False
        assert "deny" in msg.lower()

    def test_deny_decision_blocks(self):
        src = {
            "url": "https://example.com",
            "license_type": "CC BY 4.0",
            "captured_at": "2026-01-01T00:00:00Z",
            "license_decision": "deny",
        }
        ok, msg = validate_source(src)
        assert ok is False

    def test_not_on_allowlist_needs_review(self):
        src = {
            "url": "https://example.com",
            "license_type": "custom-license",
            "captured_at": "2026-01-01T00:00:00Z",
            "license_decision": "needs_review",
        }
        ok, msg = validate_source(src)
        assert ok is False
        assert "needs" in msg.lower()


class TestContentSimilarity:
    """Content similarity and dedup tests."""

    def test_identical_texts(self):
        assert text_similarity("hello world", "hello world") == 1.0

    def test_empty_texts(self):
        assert text_similarity("", "") == 0.0
        assert text_similarity("hello", "") == 0.0

    def test_similar_texts(self):
        sim = text_similarity(
            "小明有 5 顆蘋果，吃了 2 顆",
            "小明有 5 顆蘋果，吃了 3 顆",
        )
        assert 0.8 < sim < 1.0

    def test_different_texts(self):
        sim = text_similarity(
            "計算 3/4 ÷ 1/2",
            "一張地圖的比例尺為 1:50000",
        )
        assert sim < 0.5


class TestSimilarityAgainstBank:
    """Bank-level dedup checks."""

    def test_unique_question(self):
        bank = ["小明有 5 顆蘋果", "計算 3/4 ÷ 1/2"]
        is_unique, sim, idx = check_similarity_against_bank(
            "一張地圖的比例尺為 1:50000", bank
        )
        assert is_unique is True
        assert idx is None

    def test_duplicate_detected(self):
        bank = ["小明有 5 顆蘋果，吃了 2 顆，還剩幾顆？"]
        is_unique, sim, idx = check_similarity_against_bank(
            "小明有 5 顆蘋果，吃了 2 顆，還剩幾顆？", bank
        )
        assert is_unique is False
        assert idx == 0
        assert sim >= 0.85

    def test_empty_bank(self):
        is_unique, sim, idx = check_similarity_against_bank("any question", [])
        assert is_unique is True


class TestTextbookReproduction:
    """Textbook reproduction detection tests."""

    @pytest.mark.parametrize("text", [
        "第 3 課的練習題",
        "課本第 25 頁",
        "習作第 10 題",
        "翰林版數學",
        "南一出版的教材",
        "康軒數學",
        "教科書第三章",
        "某出版社出版",
    ])
    def test_textbook_patterns_detected(self, text):
        is_safe, pattern = check_textbook_reproduction(text)
        assert is_safe is False
        assert pattern is not None

    def test_clean_content(self):
        is_safe, pattern = check_textbook_reproduction(
            "小明以時速 12 公里走了 30 分鐘"
        )
        assert is_safe is True
        assert pattern is None


class TestEvidenceAndMetadata:
    """Evidence hash and metadata building tests."""

    def test_evidence_hash_deterministic(self):
        h1 = create_evidence_hash("content")
        h2 = create_evidence_hash("content")
        assert h1 == h2

    def test_evidence_hash_different_content(self):
        h1 = create_evidence_hash("content A")
        h2 = create_evidence_hash("content B")
        assert h1 != h2

    def test_build_source_metadata(self):
        meta = build_source_metadata(
            url="https://market.cloud.edu.tw/example",
            license_type="CC BY 4.0",
        )
        assert meta["url"] == "https://market.cloud.edu.tw/example"
        assert meta["license_type"] == "CC BY 4.0"
        assert meta["license_decision"] == "allow"
        assert "captured_at" in meta

    def test_build_source_metadata_with_snapshot(self):
        meta = build_source_metadata(
            url="https://example.com",
            license_type="CC0",
            content_snapshot="some content",
        )
        assert "evidence_snapshot" in meta
        assert len(meta["evidence_snapshot"]) == 64  # SHA-256 hex
