# Abhishek S — Motor Vehicle Insurance E2E Walkthrough

Real-user and QA automation path for **Abhishek S** (`kashyapabhi688@gmail.com`, `+91-9621482434`) with PDF and ZIP evidence uploads.

## Where documents are stored

| Layer | Location |
|-------|----------|
| **Object storage** | MinIO bucket `lexflow-local-documents` |
| **Console** | http://localhost:9001 — login `lexflow` / `lexflowsecret` |
| **Object key pattern** | `{firm_id}/{case_id}/{document_id}/v1/{filename}` |
| **Upload flow** | API presigned PUT → confirm → Celery OCR → WF-02 webhook |

Example: after upload, browse **Buckets → lexflow-local-documents** and search by case or document UUID.

## Sample files (repo)

Generated under:

`docs/sample-cases-test/documents/abhishek/`

| File | Purpose |
|------|---------|
| `Police_Report.pdf` | FIR BLR-TRAFFIC-2026-03412 — routes to **Local Police Traffic Division** |
| `Insurance_Claim_Form.pdf` | HDFC ERGO claim — routes to **Insurance Claims Adjuster** |
| `Vehicle_Photos.zip` | Damage photo manifest — routes to **Accident Reconstruction Unit** |
| `Medical_Report.pdf` | Manipal outpatient — routes to **Medical Records Department** |
| `Driver_License.pdf` | KA licence copy — routes to **DMV / Licensing Authority** |

Regenerate anytime:

```bash
docker compose exec api python scripts/generate_abhishek_sample_docs.py
```

## One-time setup

```bash
make dev
make migrate && make seed && make seed-sprint4 && make seed-sprint5
make seed-abhishek-case    # client + sample PDFs/zip
make seed-workflows && make n8n-import
```

Portal login: `jane@example.com` / `password123`

## Manual portal walkthrough (real user)

1. **Clients** → confirm **Abhishek S** with email and phone.
2. **Cases → New case** → client Abhishek S, title *Motor Vehicle Insurance Claim*, practice area *Litigation*.
3. **Documents** tab → upload all five files from `docs/sample-cases-test/documents/abhishek/`.
4. Wait for OCR badges to show **completed** (PDFs via PyMuPDF; zip via manifest extraction).
5. **Timeline** → verify authority events (`authority.police.notified`, etc.).
6. **AI Summary** → generate → edit → approve.
7. **Workflows** (case) → confirm **WF-02 · Document Upload Pipeline** executions (not failed).
8. **Operations** dashboard → Celery healthy, no new WF-02 404 failures.

## Automated QA (quality engineer)

```bash
make qa-abhishek-case
```

Checks: login, client, case create, 5 uploads, OCR, pipeline stages, WF-02 runs, authority timeline, AI summary, audit, notifications, ops dashboard.

## WF-02 intermittent failures — fix

**Symptom:** `document-upload-v1` webhook HTTP 404 when Celery fires before n8n is ready.

**Fix:** `_post_n8n` in `workflow_tasks.py` retries up to 4 times with exponential backoff on 404/502/503/504.

If failures persist:

```bash
make n8n-import
make cleanup-operations
docker compose logs worker --tail=50 | grep -i n8n
```

## Notifications

| Recipient | Behaviour |
|-----------|-----------|
| **Authorities** (police, insurance, medical, DMV, photos) | Timeline event + internal log (`AUTHORITY_NOTIFICATION`) |
| **Client** `kashyapabhi688@gmail.com` | **Gmail SMTP** when `GMAIL_USER` + `GMAIL_APP_PASSWORD` are set in `.env` |
| **Admin** | Gmail SMTP to `ADMIN_NOTIFICATION_EMAILS` |

### Gmail setup (`.env`)

```bash
GMAIL_USER=clawtbot@gmail.com
GMAIL_APP_PASSWORD=<16-char Google app password>
```

Restart after changes:

```bash
docker compose restart api worker
```

Verify delivery:

```bash
docker compose logs worker 2>&1 | grep -E 'EMAIL_SENT|EMAIL_FAILED|CLIENT_EMAIL'
```

If SMTP is not configured, emails fall back to log stubs (`EMAIL_STUB`).

## Incident → authority mapping

| Document title contains | Authority | Timeline event |
|-------------------------|-----------|----------------|
| police | Local Police Traffic Division | `authority.police.notified` |
| insurance, claim | Insurance Claims Adjuster | `authority.insurance.notified` |
| medical, hospital | Medical Records Department | `authority.medical.notified` |
| license, driver | DMV / Licensing Authority | `authority.dmv.notified` |
| vehicle, photo | Accident Reconstruction Unit | `authority.photos.notified` |
