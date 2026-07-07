# Complex Case — End-to-End Walkthrough

**Cyber Security Data Breach (Acme Corporation / CYB-2026-0045)**

```bash
make seed          # Acme Corporation client
make qa-complex-case
```

---

## Story

Acme Corporation suffered a LockBit ransomware attack (March 2026). ~847 customer records exposed. FMG engaged as outside counsel. Documents span incident response, forensics, insurance, vendor liability, and regulatory exposure.

---

## Documents (`documents/complex/`)

| File | Content |
|------|---------|
| `incident_report.txt` | Attack timeline, 847 records, LockBit 3.0 |
| `security_audit.txt` | Prior Veritas audit — VPN/MFA gaps |
| `firewall_logs.txt` | Exfiltration IPs, IOCs |
| `email_threads.txt` | Internal discovery, FMG engagement |
| `vendor_contract.txt` | CloudSecure MSP SLA, breach duties |
| `cyber_insurance_policy.txt` | $5M CyberGuard policy, exclusions |
| `customer_complaint.txt` | Customer AG/FTC complaint |
| `forensic_report.txt` | CrowdStrike timeline, remediation |

---

## Flow

```
Acme breach → 8 forensic/legal docs uploaded
    → OCR → Chunk/index → AI Executive Summary
    → Human approval → n8n workflows → Admin alerts → Audit
```

---

## Pass criteria

| Step | Expected |
|------|----------|
| Client | Acme Corporation, contact@acme.example |
| Case | Practice area `corporate`, priority `urgent` |
| Documents | 8 files, OCR completed |
| AI | Timeline, PII, insurance, regulatory, risk sections |
| Pipeline | 7 stages through Completed |

See [test-case-complex.md](./test-case-complex.md)
