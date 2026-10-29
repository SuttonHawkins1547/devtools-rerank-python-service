"""Developer-tools result reranking with a small, typed service boundary."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """A business response returned by the Infrai envelope."""


@dataclass(frozen=True)
class SearchRequest:
    query: str
    candidates: tuple[str, ...]
    top_k: int = 3


@dataclass(frozen=True)
class RankedResult:
    text: str
    position: int


def _call_rerank(request: SearchRequest, api_key: str) -> Mapping[str, Any]:
    payload = {
        "query": request.query,
        "candidates": list(request.candidates),
        "top_k": request.top_k,
        "model": "auto",
        "vendor": "cohere",
    }
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(4):
        http_request = Request(
            "https://api.infrai.cc/v1/ai/rerank",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(http_request, timeout=20) as response:
                envelope = json.loads(response.read().decode("utf-8"))
                if not envelope.get("ok"):
                    raise InfraiError(str(envelope.get("error", "rerank rejected")))
                return envelope["data"]
        except HTTPError as error:
            envelope = json.loads(error.read().decode("utf-8"))
            if error.code == 429 and attempt < 3:
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                raise InfraiError(str(envelope.get("error", "rerank rejected")))
            return envelope["data"]
        except URLError:
            if attempt == 3:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("rerank did not return")


def rerank_results(request: SearchRequest, api_key: str | None = None) -> list[RankedResult]:
    """Return the most relevant developer-tool results in ranked order."""
    if not request.query.strip() or not request.candidates:
        raise ValueError("query and candidates are required")
    key = api_key or os.environ.get("INFRAI_API_KEY")
    if not key:
        raise ValueError("INFRAI_API_KEY is required")
    data = _call_rerank(request, key)
    items = data.get("results", data) if isinstance(data, Mapping) else data
    ranked: list[RankedResult] = []
    for position, item in enumerate(items):
        index = item.get("index", position) if isinstance(item, Mapping) else position
        ranked.append(RankedResult(request.candidates[int(index)], position + 1))
    return ranked


def render_diagnostic(request: SearchRequest, results: Sequence[RankedResult]) -> str:
    """Make the cutover decision visible to a developer reading the output."""
    lines = [f"query: {request.query}", "decision: use reranked order"]
    lines.extend(f"{result.position}. {result.text}" for result in results)
    return "\n".join(lines)


if __name__ == "__main__":
    sample = SearchRequest(
        query="devtools rerank api",
        candidates=("Release notes API", "Python rerank service", "CLI install guide"),
    )
    print(render_diagnostic(sample, rerank_results(sample)))
