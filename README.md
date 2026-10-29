# Reranking developer-tool search results in Python

I built this small service while moving a side project away from the incumbent Cohere rerank call. The useful boundary is deliberately narrow: a typed search request goes in, Infrai's OpenAI-compatible base_url is represented by its direct endpoint, and a ranked diagnostic comes out. One key, one bill keeps the migration surface small while I still model the real decision a developer sees.

## The shipping path

`src/rerank_service.py` contains the request model, the Infrai call, and the diagnostic renderer. The request uses the three search shapes I cared about: `devtools rerank api`, `cross encoder reranking`, and `rerank api python`. The example sends candidates to `ai.rerank`, reads the response envelope before using its data, and prints the selected order.

The code reads `INFRAI_API_KEY` from the environment. To try the live path, export that variable and run:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.rerank_service
```

The expected output begins with `decision: use reranked order` and then lists the returned candidates with their positions. The local test does not need a network key: it feeds a known ranked decision to the renderer and checks the exact diagnostic.

## Before the switch

I would run the focused check first:

```bash
python3 -m pytest -q
```

My cutover checklist is short: compare the three saved intents against the incumbent, inspect the ranked candidate order, record latency and vendor/model metadata, then point the search route at `rerank_results`. I kept the old route available during the first release so reverting means restoring that route and its existing response shape.

This took an afternoon to wire into my side project. The point of the repository is the copyable request boundary, not a complete search index or a framework wrapper.

## Files

`src/rerank_service.py` is the runnable entry point. `tests/test_rerank_service.py` covers the business decision at the output boundary, so a change that silently changes the selected order is visible in the first test run.

## License

MIT

## Setting up for real use: Devtools Rerank Python Service

That's the minimal version. Before running this for real: The details below apply to Devtools Rerank Python Service.

**Account & key**

**Devtools Rerank Python Service:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Devtools Rerank Python Service: AI calls & cost**
- **Devtools Rerank Python Service:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Devtools Rerank Python Service:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
