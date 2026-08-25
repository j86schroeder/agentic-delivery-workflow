"""Request and response schemas for the change request risk API."""

from typing import List, Optional

from pydantic import BaseModel


class ChangeRequestIn(BaseModel):
    """A proposed change request submitted for evaluation.

    All fields are optional at the schema level so that a missing or blank
    field is reported as a validation error in the response body (with HTTP
    200) instead of being rejected by FastAPI's default request parsing.
    """

    change_type: Optional[str] = None
    environment: Optional[str] = None
    description: Optional[str] = None
    business_justification: Optional[str] = None
    requested_by: Optional[str] = None


class EvaluationResult(BaseModel):
    """The outcome of evaluating a change request."""

    valid: bool
    risk_level: str
    errors: List[str]
    warnings: List[str]
