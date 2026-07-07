# Simple Case — End-to-End Walkthrough

**Motor Vehicle Insurance Claim (John Doe)**

Run this demo after:

```bash
make dev          # or: docker compose up -d --build  (rebuild after API/web changes)
make migrate
make seed && make seed-sprint4 && make seed-sprint5 && make seed-demo-data
```

Automated smoke: `make qa-simple-case` (API walkthrough using sample documents).

---

## Flow

```
John Doe → Accident → Insurance Claim → Attorney opens case
    → Police Report + Medical Report + Insurance Letter
    → Upload → OCR → AI Summary → Attorney edits → Approve → Audit → Notification
```

---

## Step 1 — Sign in as Attorney

| Field | Value |
|-------|-------|
| URL | http://localhost:3000/login |
| Email | `jane@example.com` |
| Password | `password123` |

---

## Step 2 — Client (John Doe)

1. Go to **Clients**
2. If **John Doe** is not listed, run `make seed-simple-case` or create manually:
   - Name: John Doe
   - Type: Individual
   - Email: john.doe@gmail.com
   - Phone: +1-404-555-0101

---

## Step 3 — Open the case

1. **Cases** → **New case**
2. Client: **John Doe**
3. Title: **Motor Vehicle Accident Claim**
4. Practice area: **Litigation**
5. Case number is assigned automatically (e.g. `2026-00001`)

---

## Step 4 — Upload documents

1. Open the case → **Documents** tab
2. Upload these files from `docs/sample-cases-test/documents/`:

| File | Purpose |
|------|---------|
| `police_report.txt` | Incident details, parties, officer report |
| `medical_report.txt` | Injuries, treatment, medical costs |
| `insurance_letter.txt` | Claim denial, policy, amounts |

3. Wait until each document shows **OCR completed** (page auto-refreshes every 5s)

---

## Step 5 — AI summary

1. Open **AI** tab
2. Click **Generate case summary from documents**
3. Wait for status **draft**
4. Review structured sections:
   - Incident overview
   - People involved
   - Injuries & medical
   - Insurance & claim
   - Potential liability
   - Recommended next actions

---

## Step 6 — Attorney edits summary

1. Click **Edit draft**
2. Adjust wording (e.g. add firm-specific note under Recommended Next Actions)
3. Click **Save edits**

---

## Step 7 — Approve

1. Click **Approve**
2. Status changes to **approved**
3. Managing Partner and case participants receive **in-app notifications**

---

## Step 8 — Audit

1. Sign out → sign in as **Managing Partner**
   - Email: `partner@example.com` / `password123`
2. Open **Operations** in the sidebar → scroll to **Recent audit events**
   - (Legacy `/audit` redirects to the Operations dashboard.)
3. Confirm entries include:
   - `case.created`
   - `document.upload.confirmed`
   - `ai.summary.requested`
   - `ai.summary.updated` (if you edited)
   - `ai.summary.approved`

---

## Step 9 — Notification

1. While signed in as **partner@example.com**, check the **bell icon**
2. You should see: **AI summary approved** for the case number

---

## Pass criteria

| Step | Expected |
|------|----------|
| Client | John Doe with email/phone |
| Case | Auto case number, title, Litigation |
| Documents | 3 files, OCR completed |
| AI | Structured insurance draft |
| Edit | PATCH saves, audit `ai.summary.updated` |
| Approve | Status approved, timeline event |
| Audit | Partner sees full trail |
| Notification | Partner bell shows approval |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| John Doe missing | `make seed-simple-case` or `make seed-demo-data` |
| OCR stuck on "processing" | Celery worker down — check **Operations → Celery** health; run `docker compose up -d worker` |
| Stale API (404 on `/operations/dashboard`) | Rebuild: `docker compose up -d --build api web` |
| OCR skipped | Use `.txt` sample files (not scanned PDFs) |
| Generic AI stub | Upload all 3 docs before generating summary |
| AI job failed | Ensure worker is running; check `docker compose logs worker` |
| No audit events | Login as `partner@example.com`; audit tail is on **Operations** dashboard |
| No notification | Run `make seed-sprint5`; approve as Jane so partner is notified |

See also: [test-case-simple.md](./test-case-simple.md)
