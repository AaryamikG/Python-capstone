"""Small retrieval-quality eval: for each query, the expected document should appear in top-k
results with similarity above the configured threshold. Uses real embeddings, zero Gemini calls."""

import pytest

EVAL_CASES = [
    ("What is our company's security policy on passwords?", "security_policy.md"),
    ("How many reviewer approvals does a pull request need?", "code_review_process.md"),
    ("How do we handle customer complaints and what are the response times?", "customer_complaints_handling.md"),
    ("How much paid time off do employees get?", "employee_handbook.md"),
    ("What happens during a quarterly business review with a customer?", "customer_success_strategy.md"),
]

MIN_SIMILARITY = 0.2


@pytest.mark.parametrize("query,expected_doc", EVAL_CASES)
def test_expected_document_appears_in_top_k(full_corpus_collection, query, expected_doc):
    results = full_corpus_collection.query(
        query_texts=[query], n_results=4, include=["metadatas", "distances"]
    )
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    matches = [
        meta["doc_name"]
        for meta, distance in zip(metadatas, distances)
        if (1.0 - distance) >= MIN_SIMILARITY
    ]
    assert expected_doc in matches, f"expected {expected_doc} in top-k for {query!r}, got {matches}"


def test_out_of_scope_query_has_low_similarity_to_everything(full_corpus_collection):
    results = full_corpus_collection.query(
        query_texts=["What is the capital of France?"], n_results=3, include=["distances"]
    )
    similarities = [1.0 - d for d in results["distances"][0]]
    assert all(sim < 0.5 for sim in similarities), similarities
