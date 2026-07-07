# AI & Document Stack — Phase 1 (Dev) vs Phase 2 (Production)

## Phase 1 — Development / Low Cost

```
FastAPI
    │
PyMuPDF          ← born-digital PDF text extraction
    │
PaddleOCR        ← scanned PDFs & images (optional; worker `[ocr]` extra)
    │
Ollama           ← Qwen 2.5 / Llama 3 chat + nomic-embed-text
    │
PostgreSQL + pgvector   ← document chunks + embeddings
```

| Component | Config | Default (local) |
|-----------|--------|-----------------|
| OCR provider | `OCR_PROVIDER=local` | PyMuPDF → PaddleOCR fallback |
| LLM | `LLM_PROVIDER=ollama` | `qwen2.5:latest` |
| Embeddings | `EMBEDDING_ENABLED=true` | Ollama `nomic-embed-text` |
| Vector store | pgvector | `documents.document_chunks` |

### Local setup

```bash
cp .env.example .env
docker compose up -d --build
make migrate

# Pull Ollama models (first time)
docker compose exec ollama ollama pull qwen2.5:latest
docker compose exec ollama ollama pull nomic-embed-text

make seed && make seed-sprint4 && make seed-sprint5
make qa-simple-case
```

### Without Ollama

Set `LLM_PROVIDER=stub` and `EMBEDDING_ENABLED=false` in `.env` — OCR and chunking still work; AI uses deterministic stub summaries.

### Without PaddleOCR

PyMuPDF handles born-digital PDFs and `.txt` files. Set `OCR_ENABLE_PADDLE=false` or omit the `[ocr]` extra on the worker image.

---

## Phase 2 — Production

```
FastAPI
    │
Azure AI Document Intelligence   ← OCR_PROVIDER=azure_di
    │
Azure OpenAI (or Ollama for selected tasks)
    │
Azure AI Search / pgvector
    │
PostgreSQL
```

| Component | Config | Notes |
|-----------|--------|-------|
| OCR | `OCR_PROVIDER=azure_di` | Requires `AZURE_DI_*` secrets |
| LLM | `LLM_PROVIDER=azure_openai` | Primary in production |
| Hybrid LLM | Template `llm_config.provider=ollama` | Selected tasks only |
| Search | Azure AI Search + pgvector | RAG retrieval (Phase 2+) |

See [PRODUCTION-DEPLOYMENT-CHECKLIST.md](../14-playbooks/PRODUCTION-DEPLOYMENT-CHECKLIST.md) for Azure secret wiring.

---

## Pipeline flow

1. **Upload confirm** → Celery `process_document_ocr`
2. **OCR** → `ocr.factory.extract_text()` (local or Azure DI)
3. **Chunk** → 512-token windows with overlap
4. **Embed** → Ollama embeddings API → `documents.document_chunks`
5. **AI summary** → Ollama / Azure OpenAI / stub via `llm.factory`
6. **Context** → `case_context` concatenates OCR text (vector RAG retrieval: Phase 2)

---

## Environment variables

| Variable | Phase | Description |
|----------|-------|-------------|
| `OCR_PROVIDER` | 1/2 | `local` or `azure_di` |
| `OCR_ENABLE_PADDLE` | 1 | PaddleOCR fallback for scans |
| `LLM_PROVIDER` | 1/2 | `ollama`, `stub`, `azure_openai` |
| `OLLAMA_BASE_URL` | 1 | e.g. `http://ollama:11434` |
| `OLLAMA_CHAT_MODEL` | 1 | e.g. `qwen2.5:latest` |
| `OLLAMA_EMBEDDING_MODEL` | 1 | e.g. `nomic-embed-text` |
| `EMBEDDING_ENABLED` | 1 | Store pgvector chunks |
| `EMBEDDING_DIMENSIONS` | 1/2 | Default `768` (nomic-embed-text) |
| `AZURE_DI_ENDPOINT` | 2 | Document Intelligence endpoint |
| `AZURE_DI_API_KEY` | 2 | Document Intelligence key |
