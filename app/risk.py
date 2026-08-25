"""Validation and risk evaluation for change requests.

Kept as plain functions, independent of the HTTP layer, so the business
rules can be unit tested directly and read as a single, small module.
"""

from typing import Optional

from app.models import ChangeRequestIn, EvaluationResult

# Fields every change request must supply a non-blank value for.
REQUIRED_FIELDS = [
    "change_type",
    "environment",
    "description",
    "business_justification",
    "requested_by",
]

SUPPORTED_ENVIRONMENTS = ["development", "test", "staging", "production"]

# Baseline risk level assigned purely from the (normalized) environment.
RISK_BASELINE = {
    "development": "low",
    "test": "low",
    "staging": "medium",
    "production": "high",
}

# Ordered from least to most severe, used to "bump" a risk level by one step.
RISK_ORDER = ["low", "medium", "high"]

# A justification shorter than this many non-whitespace characters is weak.
MIN_JUSTIFICATION_CHARS = 20

# A justification with fewer than this many words is weak.
MIN_JUSTIFICATION_WORDS = 4


def _is_blank(value: Optional[str]) -> bool:
    return value is None or not value.strip()


def is_weak_justification(text: str) -> bool:
    """A justification is weak if it is short in characters or in words.

    Assumes the caller has already ruled out a missing/blank value, which is
    treated as a validation error rather than a weakness warning.
    """

    non_whitespace_chars = len("".join(text.split()))
    word_count = len(text.split())
    return non_whitespace_chars < MIN_JUSTIFICATION_CHARS or word_count < MIN_JUSTIFICATION_WORDS


def _bump_risk_level(level: str) -> str:
    """Raise a risk level by one step, capped at the highest level."""

    index = RISK_ORDER.index(level)
    return RISK_ORDER[min(index + 1, len(RISK_ORDER) - 1)]


def evaluate_change_request(change_request: ChangeRequestIn) -> EvaluationResult:
    """Validate a change request and determine its risk level.

    Multiple problems are collected together rather than stopping at the
    first one found.
    """

    errors = []
    warnings = []

    for field_name in REQUIRED_FIELDS:
        if _is_blank(getattr(change_request, field_name)):
            errors.append(f"{field_name} is required")

    normalized_environment = None
    if not _is_blank(change_request.environment):
        normalized_environment = change_request.environment.strip().lower()
        if normalized_environment not in SUPPORTED_ENVIRONMENTS:
            errors.append(
                "environment '"
                + change_request.environment
                + "' is not supported; must be one of: "
                + ", ".join(SUPPORTED_ENVIRONMENTS)
            )
            normalized_environment = None

    weak_justification = False
    if not _is_blank(change_request.business_justification):
        weak_justification = is_weak_justification(change_request.business_justification)
        if weak_justification:
            warnings.append(
                "business_justification is weak; provide at least "
                f"{MIN_JUSTIFICATION_CHARS} characters and {MIN_JUSTIFICATION_WORDS} words "
                "of detail"
            )

    # Fall back to the lowest baseline when the environment is missing or
    # unsupported, since a risk level is always returned even for an
    # otherwise-invalid request.
    baseline_risk = RISK_BASELINE.get(normalized_environment, "low")
    risk_level = _bump_risk_level(baseline_risk) if weak_justification else baseline_risk

    return EvaluationResult(
        valid=len(errors) == 0,
        risk_level=risk_level,
        errors=errors,
        warnings=warnings,
    )
