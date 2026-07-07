# QA Test Results — Sample Cases

Automated API walkthroughs for simple, medium, and complex real-world scenarios.

## Run

```bash
make dev && make migrate && make seed && make seed-sprint4 && make seed-sprint5
make seed-simple-case    # John Doe
make seed-demo-data      # Sarah Johnson + demo clients
make qa-all-cases        # all three (sequential, ~6–10 min)
```

Individual:

```bash
make qa-simple-case   # Motor vehicle insurance — 3 docs
make qa-medium-case   # Wrongful termination — 5 docs
make qa-complex-case  # Ransomware breach — 8 docs
```

## Document locations

| Case | Folder | Files |
|------|--------|-------|
| Simple | `documents/` | police_report, medical_report, insurance_letter |
| Medium | `documents/medium/` | employment_contract, termination_letter, email_conversation, salary_slips, employee_handbook |
| Complex | `documents/complex/` | incident_report, security_audit, firewall_logs, email_threads, vendor_contract, cyber_insurance_policy, customer_complaint, forensic_report |

## Pass criteria (each case)

1. Attorney login
2. Client exists with contact fields
3. Fresh case created with correct practice area
4. All documents uploaded + OCR completed
5. 7-stage processing pipeline
6. AI summary draft with expected sections
7. Edit + approve summary
8. Partner audit trail
9. Partner notification
10. Operations dashboard / Celery healthy

## Latest run (2026-07-07)

**Combined: 3/3 passed** (`make qa-all-cases`, ~62s)

| Case | Result | PASS | WARN | FAIL | Notes |
|------|--------|------|------|------|-------|
| Simple | PASS | 17 | 0 | 0 | 6/6 AI sections (insurance stub path) |
| Medium | PASS | 18 | 1 | 0 | Stub LLM — 3/6 sections (WARN only) |
| Complex | PASS | 21 | 1 | 0 | Stub LLM — 2/8 sections (WARN only) |

### Fixes applied

1. **AI summary race** — `await self._session.commit()` before `generate_ai_summary.delay()` in `ai_service.py` (worker could not see uncommitted summary row).
2. **Migration 005** — `document_chunks` table required for OCR/embeddings.
3. **QA login rate limit** — retry with backoff on HTTP 429 (10 logins/min per IP).
4. **AI wait timeout** — scales with document count: `max(90, doc_count * 25)`.

### Known warnings (non-blocking)

- `LLM_PROVIDER=stub` in local `.env` — medium/complex get generic stub summaries, not document-rich sections.
- Ollama `nomic-embed-text` not pulled — embedding warnings in worker logs; OCR still completes.
- Spec gaps (practice area enums, case number format, PDF vs `.txt` samples) — documented per-case in script output.
