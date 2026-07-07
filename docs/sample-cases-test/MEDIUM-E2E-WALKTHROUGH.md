# Medium Case — End-to-End Walkthrough

**Employment Wrongful Termination (Sarah Johnson / TechNova Inc.)**

```bash
make seed-demo-data
make qa-medium-case
```

---

## Story

Sarah Johnson, Senior Product Analyst at TechNova Inc., was terminated Feb 28 2026 for alleged performance issues — days after disputing PTO carryover with HR. Firm investigates wrongful termination, notice-period breach, and handbook violations.

---

## Documents (`documents/medium/`)

| File | Content |
|------|---------|
| `employment_contract.txt` | $95k salary, 30-day notice, at-will clause |
| `termination_letter.txt` | Immediate termination, PIP reference |
| `email_conversation.txt` | PTO dispute thread (Jan 2026) |
| `salary_slips.txt` | Dec 2025 – Jan 2026 pay records |
| `employee_handbook.txt` | Progressive discipline, termination policy |

---

## Flow

```
Sarah Johnson → TechNova termination → Upload 5 docs
    → OCR → AI Summary (employer, violations, risk)
    → Attorney edit → Approve → Audit → Partner notification
```

---

## Pass criteria

| Step | Expected |
|------|----------|
| Client | Sarah Johnson, sarah.j@example.com |
| Case | Practice area `employment`, priority normal |
| Documents | 5 files, OCR completed |
| AI | Sections covering termination, notice, violations |
| Approve | Partner notified |

See [test-case-medium.md](./test-case-medium.md)
