"""FastAPI application exposing the change request risk API."""

from fastapi import FastAPI

from app.models import ChangeRequestIn, EvaluationResult
from app.risk import evaluate_change_request

app = FastAPI(
    title="Change Request Risk API",
    description="Evaluates proposed change requests for completeness and risk.",
)


@app.get("/health")
def health() -> dict:
    """Liveness check."""

    return {"status": "ok"}


@app.post("/change-requests/evaluate", response_model=EvaluationResult)
def evaluate(change_request: ChangeRequestIn) -> EvaluationResult:
    """Evaluate a change request for validity and risk level.

    Always returns HTTP 200: business-rule outcomes (missing fields, an
    unsupported environment, a weak justification) are reported in the
    response body via `valid`, `errors`, and `warnings` rather than as an
    HTTP error status. Only a request body that cannot be parsed as JSON
    falls through to FastAPI's default error response.
    """

    return evaluate_change_request(change_request)
