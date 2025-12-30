# src/ollama_simple_cli.py
# pip install ollama

from __future__ import annotations
import os
from pathlib import Path
import sys
from time import time
import ollama  # official package
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL")
TEMP = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
DEFAULT_SYSTEM = (
    "You are a concise, helpful assistant. "
    "Follow instructions exactly. If asked for structured output (e.g., JSON), "
    "return only that structure with no extra text."
)
CONTEXT_SIZE = 40960


def run(
    *,
    system: str = DEFAULT_SYSTEM,
    user: str,
    model: str = DEFAULT_MODEL,
    temp: float = TEMP,
) -> str:
    """Send system + user to an Ollama model and return the response text."""

    if len(system) + len(user) >= CONTEXT_SIZE * 0.9:
        print(
            "WARNING: Prompt length exceeds model context size. Truncation may occur."
        )

    resp = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        format="json",
        options={
            "temperature": temp,  # lower = more deterministic
        },
        think=False,
        stream=False,
    )
    return resp["message"]["content"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write('Usage: python src/ollama_simple_cli.py "<user prompt>"\n')
        sys.exit(1)

    prompt = sys.argv[1]
    try:
        out = run(user=prompt)  # uses default system + model
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
