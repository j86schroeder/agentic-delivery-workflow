"""API-level tests for the change request risk API.

Each test is written against a specific Issue #1 acceptance criterion; the
test's docstring/name says which one.
"""

import copy

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "change_type": "firewall",
    "environment": "production",
    "description": "Allow application servers to reach the vendor API",
    "business_justification": "Required for the new payment integration",
    "requested_by": "operations",
}


def evaluate(payload: dict) -> dict:
    response = client.post("/change-requests/evaluate", json=payload)
    assert response.status_code == 200
    return response.json()


# --- Health endpoint -------------------------------------------------------


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Basic evaluation --------------------------------------------------


def test_valid_change_request_from_issue_example():
    body = evaluate(VALID_PAYLOAD)
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["risk_level"] == "high"  # production, strong justification


def test_response_always_includes_expected_keys():
    body = evaluate(VALID_PAYLOAD)
    assert set(body.keys()) == {"valid", "risk_level", "errors", "warnings"}


# --- Required field validation ------------------------------------------


def test_each_missing_required_field_produces_an_error():
    for field in [
        "change_type",
        "environment",
        "description",
        "business_justification",
        "requested_by",
    ]:
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload[field] = ""
        body = evaluate(payload)
        assert body["valid"] is False
        assert any(field in error for error in body["errors"]), body["errors"]


def test_missing_field_key_entirely_also_produces_an_error():
    payload = copy.deepcopy(VALID_PAYLOAD)
    del payload["requested_by"]
    body = evaluate(payload)
    assert body["valid"] is False
    assert any("requested_by" in error for error in body["errors"])


def test_multiple_validation_problems_reported_together():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["description"] = ""
    payload["requested_by"] = ""
    payload["environment"] = "sandbox"
    body = evaluate(payload)
    assert body["valid"] is False
    assert len(body["errors"]) >= 3


# --- Environment validation ----------------------------------------------


def test_unsupported_environment_produces_a_validation_error():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["environment"] = "sandbox"
    body = evaluate(payload)
    assert body["valid"] is False
    assert any("environment" in error.lower() for error in body["errors"])


def test_each_supported_environment_is_accepted():
    expected_risk_by_environment = {
        "development": "low",
        "test": "low",
        "staging": "medium",
        "production": "high",
    }
    for environment, expected_risk in expected_risk_by_environment.items():
        payload = copy.deepcopy(VALID_PAYLOAD)
        payload["environment"] = environment
        body = evaluate(payload)
        assert body["valid"] is True
        assert body["risk_level"] == expected_risk


def test_environment_matching_is_case_insensitive_and_trimmed():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["environment"] = "  Production  "
    body = evaluate(payload)
    assert body["valid"] is True
    assert body["risk_level"] == "high"


# --- Business justification -----------------------------------------------


def test_blank_business_justification_is_a_validation_error_not_a_warning():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["business_justification"] = "   "
    body = evaluate(payload)
    assert body["valid"] is False
    assert any("business_justification" in error for error in body["errors"])
    assert body["warnings"] == []


def test_short_business_justification_is_flagged_as_a_weak_warning():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["business_justification"] = "asap"  # < 20 chars and < 4 words
    body = evaluate(payload)
    assert body["valid"] is True
    assert len(body["warnings"]) == 1


def test_justification_with_enough_words_but_too_few_characters_is_weak():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["business_justification"] = "a b c d"  # 4 words, only 4 non-ws chars
    body = evaluate(payload)
    assert body["valid"] is True
    assert len(body["warnings"]) == 1


def test_justification_with_enough_characters_but_too_few_words_is_weak():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["business_justification"] = "urgentrequestneeded"  # 1 word, 20 chars
    body = evaluate(payload)
    assert body["valid"] is True
    assert len(body["warnings"]) == 1


# --- Risk level -------------------------------------------------------------


def test_production_is_higher_risk_than_non_production():
    risk_order = {"low": 0, "medium": 1, "high": 2}
    production = copy.deepcopy(VALID_PAYLOAD)
    production["environment"] = "production"

    for other_environment in ["development", "test", "staging"]:
        other = copy.deepcopy(VALID_PAYLOAD)
        other["environment"] = other_environment
        production_risk = evaluate(production)["risk_level"]
        other_risk = evaluate(other)["risk_level"]
        assert risk_order[production_risk] > risk_order[other_risk]


def test_weak_justification_raises_risk_by_one_level():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["environment"] = "development"
    payload["business_justification"] = "asap"
    body = evaluate(payload)
    assert body["risk_level"] == "medium"  # low -> medium


def test_weak_justification_bump_is_capped_at_high():
    payload = copy.deepcopy(VALID_PAYLOAD)
    payload["environment"] = "production"
    payload["business_justification"] = "asap"
    body = evaluate(payload)
    assert body["risk_level"] == "high"  # already high, stays capped
