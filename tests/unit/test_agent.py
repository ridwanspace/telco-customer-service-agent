"""Tests for agent service escalation detection."""

from __future__ import annotations

from src.agent.service import _detect_escalation


class TestDetectEscalation:
    """Tests for escalation detection logic."""

    def test_escalate_prefix_detected(self) -> None:
        reply = "ESCALATE: I cannot help with that."
        cleaned, escalate = _detect_escalation(reply)

        assert escalate is True
        assert cleaned == "I cannot help with that."

    def test_escalate_prefix_case_insensitive(self) -> None:
        reply = "escalate: Let me connect you."
        cleaned, escalate = _detect_escalation(reply)

        assert escalate is True

    def test_no_escalation_for_normal_reply(self) -> None:
        reply = "Your bill is IDR 99,000 per month."
        cleaned, escalate = _detect_escalation(reply)

        assert escalate is False
        assert cleaned == reply

    def test_phrase_based_escalation(self) -> None:
        reply = (
            "I don't have enough information to help. "
            "Let me connect you with a human agent who can help."
        )
        _, escalate = _detect_escalation(reply)

        assert escalate is True

    def test_empty_reply(self) -> None:
        reply = ""
        cleaned, escalate = _detect_escalation(reply)

        assert escalate is False
        assert cleaned == ""
