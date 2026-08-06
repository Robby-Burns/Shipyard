from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.infrastructure.exceptions import (
    generic_exception_handler,
    validation_exception_handler,
)
from app.infrastructure.middleware import RequestContextMiddleware

dummy_app = FastAPI(debug=False)
dummy_app.add_exception_handler(Exception, generic_exception_handler)
dummy_app.add_exception_handler(
    RequestValidationError, validation_exception_handler
)
dummy_app.add_middleware(RequestContextMiddleware)


@dummy_app.get("/test/error")
async def trigger_error():
    raise Exception("Simulated unhandled system error")


class SamplePayload(BaseModel):
    name: str
    age: int = Field(gt=0)


@dummy_app.post("/test/validation")
async def trigger_validation(payload: SamplePayload = Body(...)):
    return payload


dummy_client = TestClient(dummy_app, raise_server_exceptions=False)


def test_generic_exception_handler():
    custom_request_id = "test-error-req-999"
    response = dummy_client.get(
        "/test/error", headers={"X-Request-ID": custom_request_id}
    )

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert (
        data["error"]["message"]
        == "An unexpected error occurred. Please try again later."
    )
    assert data["error"]["request_id"] == custom_request_id


def test_validation_exception_handler():
    custom_request_id = "test-val-req-888"
    response = dummy_client.post(
        "/test/validation",
        json={"name": "Alice", "age": -5},
        headers={"X-Request-ID": custom_request_id},
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Input validation failed"
    assert data["error"]["request_id"] == custom_request_id
    assert isinstance(data["error"]["details"], list)
