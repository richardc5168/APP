"""
tests/unit/test_pipeline_generate.py — Unit tests for generation module.

Covers:
- AgentRole system prompts
- Topic prompt availability for all 6 scenarios
- build_generation_request structure
- build_refine_feedback formatting
- create_human_review_entry structure
- Self-Refine iteration constants
"""
import pytest

from pipeline.generate import (
    ALL_TOPIC_CODES,
    MAX_SELF_REFINE_ITERATIONS,
    SYSTEM_PROMPT,
    TOPIC_PROMPTS,
    AgentRole,
    build_generation_request,
    build_refine_feedback,
    create_human_review_entry,
    generate_problem_stub,
)


class TestAgentRoles:
    """Multi-role agent architecture tests."""

    @pytest.mark.parametrize("role", [
        AgentRole.RETRIEVER,
        AgentRole.GENERATOR,
        AgentRole.VERIFIER,
        AgentRole.REFINER,
    ])
    def test_role_has_system_prompt(self, role):
        prompt = AgentRole.get_system_prompt(role)
        assert isinstance(prompt, str)
        assert len(prompt) > 10

    def test_generator_prompt_matches_system(self):
        prompt = AgentRole.get_system_prompt(AgentRole.GENERATOR)
        assert "國小五六年級" in prompt
        assert "JSON" in prompt


class TestTopicPrompts:
    """All 6 scenario prompts must be available."""

    EXPECTED_TOPICS = ["N-5-10", "N-5-11", "N-6-7", "N-6-3", "S-6-2", "D-5-1"]

    @pytest.mark.parametrize("code", EXPECTED_TOPICS)
    def test_topic_has_prompt(self, code):
        assert code in TOPIC_PROMPTS
        config = TOPIC_PROMPTS[code]
        assert "prompt" in config
        assert len(config["prompt"]) > 10

    @pytest.mark.parametrize("code", EXPECTED_TOPICS)
    def test_topic_has_verification_rules(self, code):
        config = TOPIC_PROMPTS[code]
        assert "verification" in config or "expected_answer_type" in config

    def test_all_topics_in_list(self):
        for code in self.EXPECTED_TOPICS:
            assert code in ALL_TOPIC_CODES


class TestBuildGenerationRequest:
    """Generation request builder tests."""

    def test_request_structure(self):
        req = build_generation_request("N-5-10")
        assert "system_prompt" in req
        assert "user_prompt" in req
        assert "topic_code" in req
        assert req["topic_code"] == "N-5-10"
        assert "verification_rules" in req
        assert "max_iterations" in req
        assert req["max_iterations"] == MAX_SELF_REFINE_ITERATIONS

    def test_unknown_topic(self):
        req = build_generation_request("UNKNOWN-99")
        assert isinstance(req["user_prompt"], str)
        assert req["topic_code"] == "UNKNOWN-99"


class TestBuildRefineFeedback:
    """Self-Refine feedback builder tests."""

    def test_failure_feedback(self):
        result = {
            "reasons": {
                "schema": "ok",
                "correctness": "answer -5 is negative",
                "steps": "ok",
                "license": "ok",
            }
        }
        feedback = build_refine_feedback(result)
        assert "correctness" in feedback
        assert "negative" in feedback

    def test_all_ok_no_feedback(self):
        result = {
            "reasons": {
                "schema": "ok",
                "correctness": "ok",
                "steps": "ok",
                "license": "ok",
            }
        }
        feedback = build_refine_feedback(result)
        assert feedback == ""

    def test_multiple_failures(self):
        result = {
            "reasons": {
                "schema": "missing field: id",
                "correctness": "answer is negative",
                "steps": "ok",
                "license": "injection detected",
            }
        }
        feedback = build_refine_feedback(result)
        assert "schema" in feedback
        assert "correctness" in feedback
        assert "license" in feedback


class TestCreateHumanReviewEntry:
    """Human review queue entry tests."""

    def test_entry_structure(self):
        entry = create_human_review_entry(
            problem={"id": "test"},
            topic_code="N-5-10",
            iterations=3,
        )
        assert entry["topic_code"] == "N-5-10"
        assert entry["iterations_attempted"] == 3
        assert entry["status"] == "pending"
        assert "created_at" in entry
        assert entry["problem_draft"] == {"id": "test"}

    def test_entry_with_verify_result(self):
        entry = create_human_review_entry(
            problem=None,
            topic_code="N-6-7",
            iterations=2,
            last_verify_result={"passed": False, "score": 50},
        )
        assert entry["last_verify_result"]["passed"] is False


class TestGenerateStub:
    """Stub generator should return None until LLM is configured."""

    @pytest.mark.parametrize("code", ALL_TOPIC_CODES)
    def test_stub_returns_none(self, code):
        assert generate_problem_stub(code) is None


class TestConstants:
    """Configuration constants validation."""

    def test_max_iterations_positive(self):
        assert MAX_SELF_REFINE_ITERATIONS >= 1

    def test_system_prompt_has_rules(self):
        assert "topic_codes" in SYSTEM_PROMPT
        assert "confidence" in SYSTEM_PROMPT
