# agent-monitor

A small queue in front of a local LLM (tested against [Ollama](https://ollama.com)), so you can see
what the model layer is actually doing — separate from the hardware metrics the rest of this repo covers.

Not MLflow. This isn't experiment tracking; it's a thin proxy that answers three questions:
how many requests is the model serving right now, how many are waiting for a slot, and how
many tokens is it actually chewing through.

## What it exposes

`POST /generate` — proxies to `${OLLAMA_URL}/api/generate` (non-streaming), tracked through an
`asyncio.Semaphore(AGENT_MONITOR_SLOTS)` so only `AGENT_MONITOR_SLOTS` requests are "loaded" at
once; anything beyond that queues and counts as "waiting" until a slot frees up.

`GET /metrics` — Prometheus exposition format:

| Metric | What it tells you |
|---|---|
| `llm_requests_inflight` | Requests currently being served (loaded) |
| `llm_requests_waiting` | Requests queued behind a full slot |
| `llm_requests_total{model,status}` | Request count, by outcome |
| `llm_tokens_prompt_total{model}` | Prompt tokens processed, from Ollama's own count |
| `llm_tokens_completion_total{model}` | Completion tokens generated, from Ollama's own count |
| `llm_request_duration_seconds{model}` | End-to-end latency histogram |
| `llm_queue_wait_seconds{model}` | Time spent waiting for a free slot before serving started |

Token counts come straight from Ollama's response (`prompt_eval_count` / `eval_count`) — the
real tokenizer for the model that's actually loaded, not an estimate from an unrelated one.

## Running it

Already wired into the top-level `docker-compose.yml` (service `agent-monitor`, scraped by
Prometheus as job `agent-monitor`). It reaches Ollama on the host via
`host.docker.internal:11434` — set by `OLLAMA_URL` and the `extra_hosts: host-gateway` entry,
which works the same way on Docker Desktop (Mac/Windows) and on Linux (Pi) with modern Docker.

```bash
curl -X POST localhost:8090/generate -d '{"model":"qwen2.5:0.5b","prompt":"hello"}'
curl localhost:8090/metrics
```

Fire a handful of concurrent requests against a single-slot instance and `llm_requests_waiting`
will visibly climb while `llm_requests_inflight` stays pinned at 1 — that's the "loaded vs.
waiting" state this whole thing exists to show.

## `token_counter.py`

Standalone script, independent of the running queue — count tokens for a file (or stdin)
against a model's real tokenizer without generating anything:

```bash
python token_counter.py some_prompt.txt --model qwen2.5:0.5b
echo "hi" | python token_counter.py
```

Works by calling `/api/generate` with `options.num_predict=0`, which stops the model right after
it evaluates the prompt — `prompt_eval_count` comes back exact, no generation cost. Note the
count includes whatever chat-template wrapping Ollama applies by default (system prompt, turn
markers) — it's the real cost of sending that prompt through, not a raw character/word count.
