# VyapaarBandhu — DPDP Act 2023 Compliance Framework

## 1. Lawful Processing Basis

Under Section 4 of the Digital Personal Data Protection Act 2023 (DPDPA), VyapaarBandhu
processes personal data on two legal bases:

### 1.1 Consent (Primary)

Business owners provide **explicit consent** via WhatsApp before any invoice data is processed.
Consent is collected during the first interaction after a CA onboards a client.

**Consent flow:**
1. CA adds client via dashboard (phone number + business name)
2. VyapaarBandhu sends a WhatsApp consent message to the client
3. Client must reply "haan" / "yes" / "agree" to grant consent
4. Consent timestamp, version, and source are recorded in the `clients` table
5. No invoice processing occurs until consent is recorded

**Consent message template:**
```
Namaste! Aapke CA ({ca_firm_name}) ne aapko VyapaarBandhu se connect kiya hai.

VyapaarBandhu ek GST document management tool hai jo:
- Aapki invoice photos se data extract karta hai
- ITC draft prepare karta hai aapke CA ke liye
- Filing deadlines ki yaad dilata hai

Iske liye hum yeh data collect karenge:
- Phone number
- GSTIN
- Invoice images aur unke financial details

Yeh data sirf aapke CA ko dikhaya jayega. Images 3 saal aur data 7 saal tak stored rahega.

Agree karne ke liye "haan" reply karein.
Cancel karne ke liye "nahi" reply karein.

Privacy policy: {privacy_policy_url}
```

### 1.2 Legitimate Use (Secondary)

Under Section 7(a) of DPDPA, the CA's professional obligation to maintain client records
for GST filing constitutes a legitimate use. This applies to data already consented to
by the business owner.

## 2. Data Collected and Purpose Limitation

| Data Category | Examples | Purpose | Retention |
|---|---|---|---|
| Identity data | Phone number, business name, owner name | Client identification, WhatsApp routing | 7 years |
| Tax identifiers | GSTIN, state code | Tax computation, interstate detection | 7 years |
| Financial data | Invoice amounts, CGST/SGST/IGST, taxable amount | ITC calculation, GSTR-3B draft | 7 years |
| Invoice images | Photos of purchase invoices | OCR extraction, audit trail | 3 years |
| CA account data | Email, ICAI membership, firm name | Authentication, branding | Account lifetime + 1 year |

**Purpose limitation:** Data is processed ONLY for GST draft preparation and filing support.
No data is used for marketing, profiling, credit scoring, or any purpose beyond GST compliance assistance.

## 3. Data Subject Rights

Under DPDPA Section 11-14, business owners (Data Principals) have:

| Right | Implementation |
|---|---|
| Right to access | WhatsApp command "mera data" returns summary of stored data |
| Right to correction | WhatsApp "edit" commands + CA dashboard override |
| Right to erasure | WhatsApp "delete mera data" triggers erasure request to CA for approval |
| Right to grievance redressal | Contact email displayed in privacy policy |
| Right to nominate | Not applicable (business data, not individual health/death data) |

**Erasure constraints:** Under GST Act Section 36, tax records must be maintained for the
period prescribed. Erasure requests are honoured only after the statutory retention period.
This is documented in the consent message.

## 4. Data Protection Officer (DPO)

Under DPDPA Section 8(8), a Significant Data Fiduciary must appoint a DPO.
VyapaarBandhu designates a DPO responsible for:

- Responding to data subject requests within 72 hours
- Maintaining the Register of Processing Activities
- Conducting periodic data protection impact assessments
- Reporting breaches to the Data Protection Board of India

DPO contact information is published on the platform and in the privacy policy.

## 5. Breach Notification

Under DPDPA Section 8(6):

- **Timeline:** Notify the Data Protection Board of India within 72 hours of becoming aware of a breach
- **Affected parties:** Notify affected Data Principals (business owners and CAs) without undue delay
- **Content:** Nature of breach, data affected, remedial measures taken
- **Audit log:** The cryptographic hash chain on the audit_log table provides tamper-evident records for breach investigation

## 6. Cross-Border Data Transfer

Under DPDPA Section 16:

- All data is stored on India-region infrastructure (ap-south-1 or equivalent)
- No data is transferred outside India
- Cloud service providers (PostgreSQL, Redis, object storage) must have India-region data centres
- This is enforced at the infrastructure level (Terraform/deployment config)

## 7. Technical Safeguards

| Measure | Implementation |
|---|---|
| Encryption at rest | PostgreSQL with storage-level encryption, S3/MinIO server-side encryption |
| Encryption in transit | TLS 1.2+ on all connections |
| Access control | JWT auth with CA-scoped data access, no cross-CA data visibility |
| Audit trail | Append-only audit_log with SHA-256 hash chain |
| PII masking | All logs mask phone numbers and GSTINs |
| Data minimisation | Only 9 fields extracted per invoice; raw OCR text not stored |
| Retention enforcement | Automated nightly cron deletes data past retention period |

## 8. Consent Schema Fields

Added to `vyapaar.clients` table:

```sql
consent_given_at    TIMESTAMPTZ,         -- NULL until consent received
consent_version     TEXT,                 -- e.g. 'v1.0' — tracks consent text version
consent_withdrawn_at TIMESTAMPTZ,        -- NULL unless withdrawn
```

**Processing gate:** No invoice is processed for a client where `consent_given_at IS NULL`.
The WhatsApp message router checks this before dispatching to the OCR pipeline.
