#!/usr/bin/env python3
"""Count tokens against a model's real tokenizer via Ollama, without generating anything.

Ollama's /api/generate always returns prompt_eval_count for the prompt it was
given. Passing options.num_predict=0 stops it from generating a completion,
so this is an exact count from the model's own tokenizer, not an estimate.
"""
import argparse
import sys

import httpx


def count_tokens(text: str, model: str, host: str) -> int:
    r = httpx.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": text, "stream": False, "options": {"num_predict": 0}},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("prompt_eval_count", 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="file to count; reads stdin if omitted")
    parser.add_argument("--model", default="qwen2.5:0.5b")
    parser.add_argument("--host", default="http://localhost:11434")
    args = parser.parse_args()

    text = open(args.path).read() if args.path else sys.stdin.read()
    print(count_tokens(text, args.model, args.host))
