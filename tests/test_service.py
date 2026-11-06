"""Task 6 Unit Tests for Inference Service (service/app.py).

Tests:
1. Health and readiness endpoints (GET /healthz, GET /readyz).
2. Command parsing endpoint (POST /parse) and required headers (X-Model-Version, X-Served-By).
3. Fault injection behavior (FAULT_INJECT=1 triggers HTTP 500 with {"error": "invalid_model_output"}).
4. Request schema validation and error handling.
"""

import os
import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure environment for testing
os.environ["MODEL_URI"] = "models/v1"
os.environ["MODEL_VERSION"] = "v1"
os.environ["FAULT_INJECT"] = "0"

from service.app import load_model, healthz, readyz, parse, REQUIRED_KEYS, VALID_INTENTS


def run_sync(coro):
    """Drive coroutine synchronously to avoid Windows loopback socket hangs."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value
    raise RuntimeError("Coroutine yielded unexpectedly")


class MockRequest:
    """Mock FastAPI/Starlette Request object."""
    def __init__(self, data=None, raises=False):
        self._data = data
        self._raises = raises

    async def json(self):
        if self._raises:
            raise ValueError("Malformed JSON payload")
        return self._data


@pytest.fixture(scope="session", autouse=True)
def setup_model():
    """Ensure model is loaded before tests run."""
    load_model()


def test_healthz_and_readyz():
    """Test 1: Health and ready probes return HTTP 200."""
    res_health = run_sync(healthz())
    assert res_health.status_code == 200
    assert json.loads(res_health.body) == {"status": "ok"}

    res_ready = run_sync(readyz())
    assert res_ready.status_code == 200
    assert json.loads(res_ready.body) == {"status": "ready"}


def test_parse_valid_command():
    """Test 2: POST /parse returns HTTP 200, required headers, and strictly conforming 4-key JSON."""
    req = MockRequest({"text": "set an alarm for seven thirty am tomorrow"})
    res = run_sync(parse(req))

    assert res.status_code == 200

    # Check headers
    assert "x-model-version" in res.headers or "X-Model-Version" in res.headers
    version = res.headers.get("x-model-version") or res.headers.get("X-Model-Version")
    assert version == "v1"

    served_by = res.headers.get("x-served-by") or res.headers.get("X-Served-By")
    assert served_by is not None

    # Check JSON body
    data = json.loads(res.body)
    assert set(data.keys()) == REQUIRED_KEYS
    assert data["intent"] in VALID_INTENTS
    for slot in ("date", "time", "place"):
        assert data[slot] is None or isinstance(data[slot], str)


def test_fault_injection():
    """Test 3: FAULT_INJECT=1 triggers HTTP 500 with {"error": "invalid_model_output"}."""
    os.environ["FAULT_INJECT"] = "1"
    try:
        req = MockRequest({"text": "what is the weather in london"})
        res = run_sync(parse(req))
        assert res.status_code == 500
        assert json.loads(res.body) == {"error": "invalid_model_output"}
        assert "x-model-version" in res.headers or "X-Model-Version" in res.headers
        assert "x-served-by" in res.headers or "X-Served-By" in res.headers
    finally:
        os.environ["FAULT_INJECT"] = "0"


def test_invalid_request_handling():
    """Test 4: Invalid requests are handled cleanly."""
    req = MockRequest(raises=True)
    res = run_sync(parse(req))
    assert res.status_code == 400
    assert json.loads(res.body) == {"error": "invalid_json_request"}
