from src.rerank_service import RankedResult, SearchRequest, render_diagnostic


def test_diagnostic_preserves_the_rerank_decision():
    request = SearchRequest("cross encoder reranking", ("old guide", "relevant API", "other"))
    results = [RankedResult("relevant API", 1), RankedResult("old guide", 2)]

    output = render_diagnostic(request, results)

    assert output.splitlines() == [
        "query: cross encoder reranking",
        "decision: use reranked order",
        "1. relevant API",
        "2. old guide",
    ]
