import asyncio
import os
import time

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
SLOTS = int(os.environ.get("AGENT_MONITOR_SLOTS", "1"))

app = FastAPI()
semaphore = asyncio.Semaphore(SLOTS)

requests_inflight = Gauge(
    "llm_requests_inflight", "Requests currently being served by the model"
)
requests_waiting = Gauge(
    "llm_requests_waiting", "Requests queued, waiting for a free model slot"
)
requests_total = Counter(
    "llm_requests_total", "Total requests handled", ["model", "status"]
)
tokens_prompt_total = Counter(
    "llm_tokens_prompt_total", "Prompt tokens processed", ["model"]
)
tokens_completion_total = Counter(
    "llm_tokens_completion_total", "Completion tokens generated", ["model"]
)
request_duration_seconds = Histogram(
    "llm_request_duration_seconds", "End-to-end request latency", ["model"]
)
queue_wait_seconds = Histogram(
    "llm_queue_wait_seconds",
    "Time spent waiting for a free slot before serving started",
    ["model"],
)


@app.post("/generate")
async def generate(req: Request):
    body = await req.json()
    model = body.get("model", "unknown")

    queued_at = time.monotonic()
    requests_waiting.inc()
    async with semaphore:
        requests_waiting.dec()
        queue_wait_seconds.labels(model=model).observe(time.monotonic() - queued_at)

        requests_inflight.inc()
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                r = await client.post(
                    f"{OLLAMA_URL}/api/generate", json={**body, "stream": False}
                )
            r.raise_for_status()
            data = r.json()
            tokens_prompt_total.labels(model=model).inc(
                data.get("prompt_eval_count", 0)
            )
            tokens_completion_total.labels(model=model).inc(data.get("eval_count", 0))
            requests_total.labels(model=model, status="ok").inc()
            return JSONResponse(data)
        except Exception:
            requests_total.labels(model=model, status="error").inc()
            raise
        finally:
            request_duration_seconds.labels(model=model).observe(
                time.monotonic() - start
            )
            requests_inflight.dec()


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
