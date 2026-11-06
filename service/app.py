"""Task 3: Inference Service in FastAPI.

Provides:
- POST /parse (with headers X-Model-Version and X-Served-By)
- GET /healthz
- GET /readyz
- Fault injection support via FAULT_INJECT=1
- S3 / local model loading via MODEL_URI, MODEL_VERSION, S3_ENDPOINT
"""

import os
import re
import json
import socket
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

torch.set_num_threads(2)

# Configuration from environment variables
MODEL_URI = os.environ.get("MODEL_URI", "models/v1")
MODEL_VERSION = os.environ.get("MODEL_VERSION", "v1")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "http://seaweedfs-s3.data.svc.cluster.local:8333")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "40"))
FAULT_INJECT = os.environ.get("FAULT_INJECT", "0")
POD_NAME = os.environ.get("HOSTNAME", os.environ.get("POD_NAME", socket.gethostname()))

VALID_INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events"
}
REQUIRED_KEYS = {"intent", "date", "time", "place"}

# Global model state
tokenizer = None
model = None
is_ready = False


def download_from_s3(uri: str, local_dir: Path):
    """Download model files from S3/SeaweedFS if URI starts with s3://."""
    import boto3
    from urllib.parse import urlparse
    
    parsed = urlparse(uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    )
    
    local_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model artifacts from s3://{bucket}/{prefix} to {local_dir}...")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            rel_path = os.path.relpath(key, prefix)
            target_path = local_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, key, str(target_path))
            print(f"Downloaded {key} -> {target_path}")


def load_model():
    """Load model and tokenizer into memory."""
    global tokenizer, model, is_ready
    if is_ready and model is not None:
        return
    
    local_path = Path(MODEL_URI)
    if MODEL_URI.startswith("s3://"):
        cache_dir = Path("/tmp/model_cache") / MODEL_VERSION
        download_from_s3(MODEL_URI, cache_dir)
        local_path = cache_dir
    elif not local_path.exists():
        # Fallback check under models/{MODEL_VERSION}
        candidate = Path("models") / MODEL_VERSION
        if candidate.exists():
            local_path = candidate
            
    print(f"Loading model from {local_path}...", flush=True)
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(local_path), local_files_only=True)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(str(local_path))

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        model = AutoModelForCausalLM.from_pretrained(str(local_path), local_files_only=True).float()
    except Exception:
        model = AutoModelForCausalLM.from_pretrained(str(local_path)).float()

    model.eval()
    is_ready = True
    print(f"Model {MODEL_VERSION} loaded and ready on {POD_NAME}.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    yield

app = FastAPI(lifespan=lifespan)


def validate_prediction(raw: str):
    """Validate JSON against schema. Return dict if valid, else None."""
    try:
        obj = json.loads(raw.strip())
    except (json.JSONDecodeError, TypeError):
        return None
        
    if not isinstance(obj, dict):
        return None
        
    if set(obj.keys()) != REQUIRED_KEYS:
        return None
        
    if obj["intent"] not in VALID_INTENTS:
        return None
        
    for k in ("date", "time", "place"):
        val = obj[k]
        if val is not None and not isinstance(val, str):
            return None
            
    return obj


@app.get("/healthz")
async def healthz():
    """Liveness probe: HTTP 200 as long as process is alive."""
    return JSONResponse(status_code=200, content={"status": "ok"})


@app.get("/readyz")
async def readyz():
    """Readiness probe: HTTP 503 until model is loaded, HTTP 200 after."""
    if is_ready:
        return JSONResponse(status_code=200, content={"status": "ready"})
    return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.post("/parse")
async def parse(request: Request):
    """Parse a natural language command into four-key JSON."""
    headers = {
        "X-Model-Version": MODEL_VERSION,
        "X-Served-By": POD_NAME
    }
    
    if not is_ready:
        return JSONResponse(
            status_code=503,
            content={"error": "model_not_ready"},
            headers=headers
        )
        
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_json_request"},
            headers=headers
        )
        
    text = body.get("text") or body.get("command", "")
    
    prompt = f"Command: {text}\nJSON:\n"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=False
        )
        
    generated = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    
    # Check fault injection
    fault_inject = os.environ.get("FAULT_INJECT", FAULT_INJECT)
    if fault_inject == "1":
        generated = "not json"
        
    # Extract JSON object
    match = re.search(r"\{.*?\}", generated, re.DOTALL)
    raw_candidate = match.group(0) if match else generated
    
    parsed = validate_prediction(raw_candidate)
    if parsed is None:
        return JSONResponse(
            status_code=500,
            content={"error": "invalid_model_output"},
            headers=headers
        )
        
    return JSONResponse(
        status_code=200,
        content=parsed,
        headers=headers
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
