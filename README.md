# Enterprise Documentation Assistant

A multi-agent Retrieval-Augmented Generation (RAG) system for enterprise documentation. A **Manager
agent** classifies each question and routes it to a **Qualitative RAG agent** (company policy/process
documents) and/or a **Quantitative NL-to-SQL agent** (sales/customer/employee data), then returns a
clean, cited, formatted answer via a CLI or a REST API.

## Quick Start

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt && pip install -e .
copy .env.example .env   # then paste your GEMINI_API_KEY into it
python scripts/generate_sql_data.py
python scripts/build_vector_store.py
pytest                                          # run tests (fully mocked, no API calls)
python -m enterprise_rag.cli.main               # run the CLI
```

## Architecture

```
                         ┌───────────────────────────┐
   CLI (REPL / --query)  │                           │
   ──────────────────────►     ManagerAgent          │
                         │  1. classify(query)        │
   FastAPI (/query, ...) │     -> qualitative /       │
   ──────────────────────►        quantitative /      │
                         │        complex / ambiguous │
                         └─────────────┬───────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 ▼                                           ▼
     QualitativeRAGAgent                         QuantitativeSQLAgent
     - embeds query (sentence-transformers)       - introspects SQLite schema
     - top-k search in Chroma                     - Gemini: NL -> SQL
     - filters by min similarity                  - validates SQL (SELECT-only)
     - Gemini: answer grounded in chunks           - executes read-only, 1 retry on error
     - returns answer + citations                  - returns answer + SQL + rows

                 └─────────────────────┬─────────────────────┘
                                       ▼
                     complex queries: Manager merges both answers
                     into one response, labeled by section, with
                     a short synthesis connecting the findings.
```

Both entrypoints (CLI and API) call the same `enterprise_rag.core.build_manager_agent()` factory, so
agent wiring never diverges between them.

## Project Layout

```
data/
  documents/          synthetic enterprise documents (security policy, code review, etc.)
  enterprise.db        generated SQLite database (git-ignored)
  chroma/               generated vector store (git-ignored)
scripts/
  generate_sql_data.py  seeds data/enterprise.db with synthetic sales/customer/employee data
  build_vector_store.py chunks data/documents/*.md into the Chroma collection
src/enterprise_rag/
  config.py             Settings (env-based config, shared by CLI and API)
  logging_config.py      structured JSON logging
  schemas.py              shared Pydantic models
  core.py                  build_manager_agent() factory
  llm/                      Gemini client wrapper + prompts
  vectorstore/              chunking, embedding function, Chroma store helpers
  agents/                    ManagerAgent, QualitativeRAGAgent, QuantitativeSQLAgent, SQL guard
  cli/                        REPL + --query CLI
  api/                          FastAPI app, routes, schemas
tests/
  unit/                 agent-level unit tests (LLM mocked, no network)
  integration/            multi-agent workflow, CLI, retrieval-quality eval, connection checks
  api/                      FastAPI endpoint tests
```

## Requirements

- **Python 3.10+** (the rubric mentions 3.8+, but current releases of `chromadb`,
  `sentence-transformers`, and `google-genai` require 3.9/3.10+, so this project targets 3.10+;
  it has been developed and tested on Python 3.14).
- A [Gemini API key](https://aistudio.google.com/apikey) (a free-tier key works — see the note on API
  usage below).
- Internet access on first run, to download the local embedding model (`all-MiniLM-L6-v2`) from
  Hugging Face. After that, embeddings run fully offline/local.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
pip install -e .
```

Copy `.env.example` to `.env` and paste in your Gemini API key:

```bash
copy .env.example .env
```

```
GEMINI_API_KEY=your-key-here
```

> **Model availability note**: Gemini model availability varies by key (new free-tier keys in
> particular can get 404s on older model names, or transient 503 "high demand" errors on some
> current ones). `GEMINI_MODEL` in `.env` defaults to `gemini-3.5-flash-lite`, confirmed working at
> the time of writing. If you get a 404 or persistent 503, run this to see what your key can access,
> and update `GEMINI_MODEL` accordingly — no code changes needed:
> ```bash
> python -c "import os; from google import genai; c = genai.Client(api_key=os.environ['GEMINI_API_KEY']); [print(m.name) for m in c.models.list() if 'generateContent' in (m.supported_actions or [])]"
> ```

Generate the synthetic data (one-time, or whenever you want to regenerate it):

```bash
python scripts/generate_sql_data.py
python scripts/build_vector_store.py
```

## Usage

### CLI

```bash
python -m enterprise_rag.cli.main
```

```
Enterprise Documentation Assistant
Ask a question about company policy/process (qualitative) or data (quantitative).
Type :quit or :exit to leave.

> What is our company's security policy on passwords?
╭─ Qualitative (document search) ────────────────────────────────╮
│ Passwords must be at least 14 characters and are rotated every  │
│ 180 days...                                                      │
│                                                                   │
│ Sources                                                          │
│ - security_policy.md (chunk 1, similarity 0.71)                 │
╰────────────────────────────────────────── 850 ms ──────────────╯
```

Single-shot mode (useful for scripting):

```bash
python -m enterprise_rag.cli.main --query "What's our customer churn rate?"
```

### API

```bash
uvicorn enterprise_rag.api.main:app --reload
```

- `GET /health` — liveness + config check (never calls Gemini)
- `POST /query` — full manager pipeline (classify, route, answer)
- `POST /agents/qualitative` — direct RAG lookup, bypassing the classifier
- `POST /agents/quantitative` — direct NL-to-SQL lookup, bypassing the classifier
- `POST /agents/manager/classify` — classification only (debugging aid)
- Interactive docs at `/docs` (OpenAPI)

```bash
curl -X POST http://127.0.0.1:8000/query -H "Content-Type: application/json" \
  -d "{\"query\": \"Compare Q4 performance across regions\"}"
```

## Query Types

- **Qualitative**: "What is our company's security policy?", "Explain the code review process."
- **Quantitative**: "Show me monthly revenue trends.", "What's our customer churn rate?"
- **Complex** (needs both): "How does our employee satisfaction compare to industry standards and what
  policies might impact this?" — the Manager runs both agents and merges the findings into one
  labeled answer with a short synthesis.
- **Ambiguous**: anything too vague to route confidently gets a clarification question back instead of
  a guess.

## Testing

```bash
pytest
```

The entire automated suite mocks the Gemini client (`tests/fixtures/fake_gemini_client.py`) — **no
test makes a real API call**, so running it repeatedly costs nothing against a free-tier key. Chroma
and SQLite tests use ephemeral, hand-seeded temp stores for fast, deterministic results. A small
retrieval-quality eval (`tests/integration/test_retrieval_quality.py`) checks that expected documents
surface for a set of representative questions using the real local embedding model (still no API
calls).

To try the real Gemini integration end-to-end (a handful of real calls only), run the CLI or API
manually with your API key set, as shown above.

## Verified Example Queries

These have been manually run end-to-end against the real Gemini API and confirmed working:

```bash
python -m enterprise_rag.cli.main --query "What is our company's security policy on passwords?"
python -m enterprise_rag.cli.main --query "What's our customer churn rate?"
python -m enterprise_rag.cli.main --query "Compare Q4 2025 sales performance across regions"
python -m enterprise_rag.cli.main --query "How does our employee satisfaction compare to industry standards and what policies might impact this?"
python -m enterprise_rag.cli.main --query "Tell me about it"
python -m enterprise_rag.cli.main --query "What is our company's policy on office pets?"
```

| Query | Confirms |
|---|---|
| password policy | qualitative routing + citations |
| churn rate | quantitative routing + generated SQL |
| Q4 regions | multi-table `JOIN` + `GROUP BY` in generated SQL |
| satisfaction vs. benchmark | complex routing, merged answer, both agents labeled |
| "Tell me about it" | ambiguous routing, clarification question, no agent calls |
| office pets | graceful "not covered" answer instead of a fabricated policy |

## Design Notes

- **Retrieval quality**: every qualitative answer includes citations (document name, chunk id,
  similarity score); a minimum-similarity threshold (default `0.35`, see `MIN_SIMILARITY` in `.env`)
  means the agent returns "not found in knowledge base" rather than fabricating an answer when nothing
  relevant is retrieved — and it does this without spending an LLM call.
- **SQL safety**: generated SQL is restricted to a single read-only `SELECT` (or `WITH ... SELECT`)
  statement (`agents/sql_guard.py`), executed against a read-only SQLite connection. If execution
  fails, the agent retries exactly once with the database error fed back to the model, then reports a
  clean failure rather than looping.
- **Structured logging**: every agent logs the incoming query, which agent(s) handled it, retrieved
  sources or generated SQL, execution time, and errors, as JSON lines (`logging_config.py`).
- **Frugal by design**: given the free-tier Gemini key this project was built against, the code avoids
  speculative LLM calls (the "not found" and ambiguous-query paths skip the LLM entirely, retries are
  capped at one, and `/health` never touches the LLM), and the test suite never calls the real API.
