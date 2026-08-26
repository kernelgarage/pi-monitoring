#!/usr/bin/env python3
"""Count tokens against a model's real tokenizer via Ollama, without generating.

Ollama's /api/generate always returns prompt_eval_count for the prompt it was
given. Passing options.num_predict=0 stops it from generating a completion,
so this is an exact count from the model's own tokenizer, not an estimate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import typer

app = typer.Typer(add_completion=False)


def count_tokens(text: str, model: str, host: str) -> int:
    r = httpx.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": text,
            "stream": False,
            "options": {"num_predict": 0},
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("prompt_eval_count", 0)


@app.command()
def main(
    path: Path | None = typer.Argument(
        None, help="File to count; reads stdin if omitted"
    ),
    model: str = typer.Option("qwen2.5:0.5b", help="Model name, as known to Ollama"),
    host: str = typer.Option("http://localhost:11434", help="Ollama host"),
) -> None:
    text = path.read_text() if path else sys.stdin.read()
    print(count_tokens(text, model, host))


if __name__ == "__main__":
    app()
