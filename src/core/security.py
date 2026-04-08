"""Input validation and prompt injection detection.

Defense-in-depth: even if injection patterns slip through,
the system prompt structure should prevent exploitation.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt injection detection patterns
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(previous|above|all|prior|system)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(previous|above|all|prior|system)\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(your\s+)?(previous|above|all|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"override\s+(previous|above|all|prior|system)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+(instructions?|prompt|rules|config)", re.IGNORECASE),
    re.compile(r"what\s+(are|is)\s+your\s+(instructions?|prompt|rules|system)", re.IGNORECASE),
    re.compile(r"show\s+(me\s+)?your\s+(instructions?|prompt|rules)", re.IGNORECASE),
    re.compile(r"pretend\s+(to\s+be|you'?re)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a|an|if)", re.IGNORECASE),
    re.compile(r"===\s*system", re.IGNORECASE),
    re.compile(r"<<<.*>>>"),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<\|system\|>", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(your|the)\s+(rules|instructions)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
]

# Maximum allowed input length (prevent context overflow attacks)
MAX_INPUT_LENGTH = 2000


def detect_prompt_injection(user_input: str) -> bool:
    """Detect potential prompt injection patterns in user input.

    Returns True if input appears suspicious.
    """
    return any(pattern.search(user_input) for pattern in _INJECTION_PATTERNS)


def sanitize_input(user_input: str) -> str:
    """Sanitize user input by removing potential injection markers.

    Defense-in-depth: even with sanitization, the prompt structure
    should prevent exploitation via === markers and meta-instructions.
    """
    sanitized = user_input

    # Remove system instruction markers
    sanitized = re.sub(r"===\s*[A-Z\s]+===", "[redacted]", sanitized, flags=re.IGNORECASE)

    # Remove chat template delimiters
    sanitized = re.sub(r"<<<|>>>", "", sanitized)
    sanitized = re.sub(r"<\|im_start\|>|<\|im_end\|>", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\[INST\]|\[/INST\]", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(
        r"<\|system\|>|<\|user\|>|<\|assistant\|>", "", sanitized, flags=re.IGNORECASE
    )

    # Truncate to prevent context overflow
    if len(sanitized) > MAX_INPUT_LENGTH:
        sanitized = sanitized[:MAX_INPUT_LENGTH]
        logger.warning(
            "User input truncated from %d to %d chars", len(user_input), MAX_INPUT_LENGTH
        )

    return sanitized.strip()


def validate_input(user_input: str) -> tuple[str, bool]:
    """Validate and sanitize user input.

    Returns (sanitized_input, is_injection_attempt).
    """
    is_injection = detect_prompt_injection(user_input)

    if is_injection:
        logger.warning("Prompt injection detected: %s", user_input[:100])

    sanitized = sanitize_input(user_input)

    return sanitized, is_injection
