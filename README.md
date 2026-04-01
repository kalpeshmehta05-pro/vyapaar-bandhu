# VyapaarBandhu

> AI-powered GST compliance assistant for India's 8 crore small businesses.
> WhatsApp-native, Hindi/English bilingual, built for the CA who manages 50+ clients on a phone.

A CA's client sends an invoice photo on WhatsApp. VyapaarBandhu OCRs it, classifies it, calculates ITC, detects RCM liability, and prepares the GSTR-3B JSON -- ready for filing in minutes, not hours.

## Architecture

```
                         WhatsApp (Business Owner)
                                  |
                          Meta Cloud API
                                  |
                    +-------------v--------------+
                    |   FastAPI (async, uvicorn)  |
                    |   Twilio Webhook Handler    |
                    |   HMAC-SHA256 verification  |
                    +---+--------------------+----+
                        |                    |
                   Celery Task          REST API
                   (Redis broker)       (CA Dashboard)
                        |                    |
              +---------v---------+    +-----v------+
              | OCR Pipeline      |    | Next.js 14 |
              | Vision API        |    | TypeScript  |
              | + Tesseract       |    | Tailwind    |
              | fallback          |    +-----+------+
              +---------+---------+          |
                        |               Browser
              +---------v---------+
              | Invoice Classifier|
              | Keyword rules     |
              | BART zero-shot    |
              | IndicBERT         |
              +---------+---------+
                        |
              +---------v---------+
              | Compliance Engine |
              | RCM detection     |
              | ITC calculation   |
              | GSTIN validation  |
              +---------+---------+
                        |
              +---------v---------+
              | PostgreSQL 16     |
              | Async SQLAlchemy  |
              | Row-level security|
              +---------+---------+
                        |
              +---------v---------+
              | GSTR-3B Export    |
              | JSON (GSTN spec)  |
              | PDF (WeasyPrint)  |
              | Tally XML         |
              +-------------------+
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API Server | FastAPI 0.134 (async) | Native async/await, OpenAPI docs, Pydantic validation |
| ORM | SQLAlchemy 2.0 (async) | Async sessions, type-safe models, Alembic migrations |
| Database | PostgreSQL 16 | JSONB for audit data, row-level security, FOR UPDATE locking |
| Cache / Broker | Redis 7 | Session store, Celery broker, rate limit backend |
| Task Queue | Celery 5 | Async OCR processing, dead-letter queue, retry policies |
| OCR (Primary) | Google Vision API | document_text_detection, Hindi + English, high accuracy |
| OCR (Fallback) | Tesseract 5 | Free, local, Hindi + English language packs |
| Classification | BART + IndicBERT | Zero-shot GST category classification, local inference |
| Frontend | Next.js 14, TypeScript | App router, server components, static export |
| Styling | Tailwind CSS 3 | Dark theme, glass-morphism design system |
| PDF Generation | WeasyPrint | HTML-to-PDF, ITC summary tables, filing reports |
| Object Storage | MinIO (dev) / S3 (prod) | Invoice images, export artifacts, presigned URLs |
| Containerization | Docker Compose | Single-command local dev, production parity |

## Key Features

### WhatsApp-Native Invoice Ingestion

- Business owners send invoice photos directly on WhatsApp
- 7-state conversation state machine: IDLE, CONSENT, AWAITING_IMAGE, PROCESSING, REVIEW, COMPLETED, ERROR
- Bilingual support: Hindi + English templates
- DPDP Act 2023 consent gate before any data processing
- Idempotent webhook with message deduplication (SHA-256 hash)
- Twilio HMAC-SHA256 signature verification on every inbound POST

### Production-Grade OCR Pipeline

- Primary: Google Vision API (document_text_detection mode)
- Fallback: Tesseract 5 with Hindi (`hin`) + English (`eng`) language packs
- Image preprocessing: grayscale conversion, deskew, Otsu binarization, 300 DPI upscaling
- Per-field confidence scoring with named thresholds:
  - GSTIN: 0.95 (strict -- checksum validated separately)
  - Amounts: 0.90 (financial accuracy critical)
  - Dates: 0.80 (format variation tolerance)
- Dead-letter queue for failed OCR with CA notification via WhatsApp
- Concurrent processing via Celery with Redis broker

### Deterministic GST Classification Engine

- Zero AI/LLM in tax logic -- 100% deterministic rules for all tax calculations
- B2B vs B2C detection via recipient GSTIN validation
- Interstate vs intrastate via state code comparison (first 2 digits of GSTIN)
- RCM detection covering all 5 statutory categories:
  1. GTA (SAC 9965, 9967) -- Notification 13/2017-CT(R) Entry 1
  2. Legal services (SAC 9982) -- Entry 2
  3. Security services (SAC 9985) -- Entry 8
  4. Import of services (place_of_supply = 99)
  5. Unregistered vendor (GSTIN absent or invalid)
- GSTIN checksum: Modulo-36 algorithm per GSTN specification
- All tax math: Python `Decimal` with `ROUND_HALF_UP` -- never `float`

### CA Dashboard

- Real-time GSTR-3B readiness per client (0-100% ring visualization)
- ITC summary: confirmed / pending / rejected breakdown with INR formatting
- Live alert engine: red/yellow/green severity by deadline proximity + compliance flags
- Bulk invoice actions: approve, reject, flag (max 50 per request)
- Client status donut chart and ITC bar chart (Recharts)
- Animated counters, skeleton loading states, glass-morphism dark theme

### GSTR-3B Export

- Exact GSTN portal JSON schema (`ret_period: "MMYYYY"`)
- All amounts: string with exactly 2 decimal places
- `itc_net` clamped to zero (no negative ITC allowed)
- RCM liability mapped to `isup_rev.txval`
- PDF filing summary via WeasyPrint with ITC table + invoice list
- S3 upload with presigned download URLs (15-minute expiry)
- Tally XML export (basic structure)

### Security

- RS256 JWT (asymmetric keys, not HS256) with httpOnly cookies
- Row-Level Security on PostgreSQL (per-CA data isolation)
- SHA-256 hash chain on audit log (legally defensible, append-only)
- `SELECT ... FOR UPDATE` on audit writes (prevents race conditions)
- Rate limiting via slowapi:
  - Login: 5/minute per IP
  - WhatsApp webhook: 100/minute per IP
  - Invoice upload: 20/minute per CA
  - Bulk actions: 10/minute per CA
  - Exports: 30/minute per CA
- Security headers on every response: HSTS, CSP, X-Frame-Options: DENY, X-XSS-Protection
- Input sanitization: HTML tag stripping, null byte removal, length enforcement
- DPDP Act 2023 compliance: consent artifacts, withdrawal support, 72-hour breach SLA

## Local Development

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- RS256 key pair (see below)

### Generate JWT keys

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### Start everything

```bash
git clone https://github.com/kalpeshmehta05-pro/vyapaar-bandhu.git
cd vyapaar-bandhu
cp backend/.env.example backend/.env
docker compose up -d
```

### Run backend tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, API at `http://localhost:8000`.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment: development, staging, production | `development` |
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `JWT_PRIVATE_KEY_PATH` | Path to RS256 private key PEM | `keys/private.pem` |
| `JWT_PUBLIC_KEY_PATH` | Path to RS256 public key PEM | `keys/public.pem` |
| `ACCESS_TOKEN_EXPIRY` | Access token TTL in seconds | `900` (15 min) |
| `REFRESH_TOKEN_EXPIRY` | Refresh token TTL in seconds | `604800` (7 days) |
| `WA_PHONE_NUMBER_ID` | WhatsApp Business phone number ID | -- |
| `WA_ACCESS_TOKEN` | WhatsApp Cloud API access token | -- |
| `WA_APP_SECRET` | WhatsApp app secret for HMAC verification | -- |
| `WA_VERIFY_TOKEN` | Webhook verification challenge token | -- |
| `TESSERACT_CMD` | Path to Tesseract binary | `tesseract` |
| `OCR_CONFIDENCE_THRESHOLD` | Green confidence threshold | `0.85` |
| `S3_ENDPOINT_URL` | S3-compatible storage endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | S3 access key | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | `minioadmin` |
| `CELERY_BROKER_URL` | Celery broker (Redis) | `redis://localhost:6379/1` |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost:3000"]` |
| `BCRYPT_ROUNDS` | Password hashing cost factor | `12` |

## API Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/auth/register` | -- | Register new CA account |
| `POST` | `/api/v1/auth/login` | -- | Login, returns JWT + httpOnly cookie |
| `POST` | `/api/v1/auth/refresh` | Cookie | Rotate refresh token |
| `POST` | `/api/v1/auth/logout` | Cookie | Revoke refresh token, clear cookies |
| `GET` | `/api/v1/auth/me` | JWT | Get current CA profile |
| `PATCH` | `/api/v1/auth/me` | JWT | Update CA profile |
| `GET` | `/api/v1/clients/` | JWT | List all clients for CA |
| `POST` | `/api/v1/clients/` | JWT | Create new client |
| `GET` | `/api/v1/clients/{id}` | JWT | Get client details |
| `PATCH` | `/api/v1/clients/{id}` | JWT | Update client |
| `DELETE` | `/api/v1/clients/{id}` | JWT | Soft-delete client |
| `GET` | `/api/v1/clients/{id}/itc-summary` | JWT | ITC summary for period |
| `POST` | `/api/v1/invoices/upload` | JWT | Upload invoice image |
| `GET` | `/api/v1/invoices/` | JWT | List invoices (filterable) |
| `GET` | `/api/v1/invoices/{id}` | JWT | Get invoice details |
| `POST` | `/api/v1/invoices/{id}/approve` | JWT | CA approves invoice |
| `POST` | `/api/v1/invoices/{id}/reject` | JWT | CA rejects invoice |
| `POST` | `/api/v1/invoices/bulk-action` | JWT | Bulk approve/reject/flag |
| `GET` | `/api/v1/dashboard/overview` | JWT | Dashboard overview (all clients) |
| `GET` | `/api/v1/dashboard/summary` | JWT | Period ITC summary |
| `GET` | `/api/v1/dashboard/alerts` | JWT | Active compliance alerts |
| `GET` | `/api/v1/exports/gstr3b` | JWT | GSTR-3B JSON export |
| `GET` | `/api/v1/exports/pdf` | JWT | PDF filing summary |
| `GET` | `/api/v1/exports/tally` | JWT | Tally XML export |
| `GET` | `/api/v1/whatsapp/webhook` | -- | Meta verification handshake |
| `POST` | `/api/v1/whatsapp/webhook` | HMAC | Inbound WhatsApp messages |
| `GET` | `/api/v1/audit/export` | JWT | Export audit logs (date range) |
| `GET` | `/api/v1/audit/verify-chain` | JWT | Verify audit hash chain integrity |
| `GET` | `/health/live` | -- | Liveness probe |
| `GET` | `/health/ready` | -- | Readiness probe |

## Compliance Notes

### DPDP Act 2023

- **Lawful basis**: Consent-based processing (Section 6)
- **Consent artifacts**: Stored in audit log with timestamp, phone, version
- **Withdrawal**: Client can withdraw consent via WhatsApp; all processing stops
- **Breach notification**: 72-hour SLA to Data Protection Board of India
- **Data retention**: Invoice images 3 years, transactional data 7 years
- **DPO record**: Designated Data Protection Officer contact in privacy policy

### GST Compliance

- RCM under Section 9(4) CGST Act, 2017
- Notification 13/2017-CT(R) for service-specific RCM categories
- IGST Act Section 5(3) for import of services
- GSTIN validation per GSTN Modulo-36 checksum specification
- All tax amounts stored as `Decimal` with `ROUND_HALF_UP`

### Audit Trail

- SHA-256 hash chain: each row hashes previous row's ID + hash + event data
- Append-only: PostgreSQL RULE prevents UPDATE/DELETE on audit_log table
- `SELECT ... FOR UPDATE` serializes concurrent writes (no race conditions)
- Exportable via `/api/v1/audit/export` with date range filtering
- Chain integrity verifiable via `/api/v1/audit/verify-chain`
- S3 archival with Object Lock in COMPLIANCE mode (production)

## Project Status

| Phase | Name | Status | Key Deliverable |
|-------|------|--------|-----------------|
| 1 | Auth + DPDP + Audit | Done | RS256 JWT, consent gate, hash chain audit log |
| 2 | Compliance + RCM | Done | Deterministic GST rules, 5-category RCM, ITC calculator |
| 3 | OCR + Classification | Done | Vision API + Tesseract pipeline, BART + IndicBERT classifier |
| 4 | WhatsApp FSM | Done | 7-state conversation machine, bilingual templates, Twilio integration |
| 5 | Dashboard + Alerts | Done | Real-time overview, ITC summary, alert engine |
| 6 | GSTR-3B Export | Done | GSTN JSON schema, PDF via WeasyPrint, S3 presigned URLs |
| 7 | Next.js Frontend | Done | Dark theme dashboard, readiness rings, client management |
| 8 | Security Hardening | Done | Rate limiting, security headers, input sanitization, audit chain fix |
| 9 | AWS Infra + CI/CD | Planned | ECS/Fargate, RDS, ElastiCache, GitHub Actions |

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit with conventional commits: `git commit -m 'feat: add new feature'`
4. Push and open a pull request
5. Ensure all tests pass and types check (`pytest`, `npx tsc --noEmit`)

## License

This project is proprietary software. All rights reserved.
