# VyapaarBandhu Deployment Guide

This guide covers three deployment options for VyapaarBandhu, from simplest to most customizable.

## Prerequisites

- Docker and Docker Compose installed
- RS256 key pair generated (see below)
- Domain name configured (optional for local testing)

### Generate JWT Keys

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

## Option A: Railway (Recommended for MVP)

Railway offers a free $5 monthly credit, which is enough to run the backend + PostgreSQL + Redis for initial testing and demos.

### Steps

1. Install the Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Add infrastructure services:
```bash
railway add --plugin postgresql
railway add --plugin redis
```

4. Set environment variables:
```bash
railway variables set APP_ENV=production
railway variables set JWT_PRIVATE_KEY="$(cat keys/private.pem)"
railway variables set JWT_PUBLIC_KEY="$(cat keys/public.pem)"
railway variables set ALLOWED_ORIGINS='["https://your-app.railway.app"]'
railway variables set BCRYPT_ROUNDS=12
railway variables set MIN_PASSWORD_LENGTH=12
```

DATABASE_URL and REDIS_URL are auto-injected by Railway plugins.

5. Deploy:
```bash
railway up
```

6. Set custom domain (optional):
```bash
railway domain
```

7. Run database migrations:
```bash
railway run alembic upgrade head
```

### Deploying Frontend to Vercel

For best performance, deploy the frontend separately to Vercel:

```bash
cd frontend
npx vercel --prod
```

Set the environment variable in Vercel:
- `NEXT_PUBLIC_API_URL`: Your Railway backend URL + `/api/v1`

## Option B: Self-Hosted VPS

For a VPS on Hetzner (EUR 4.5/month) or DigitalOcean ($6/month):

### Steps

1. SSH into your server:
```bash
ssh root@your-server-ip
```

2. Install Docker and Docker Compose:
```bash
curl -fsSL https://get.docker.com | sh
```

3. Clone the repository:
```bash
git clone https://github.com/kalpeshmehta05-pro/vyapaar-bandhu.git
cd vyapaar-bandhu
```

4. Create environment file:
```bash
cp backend/.env.example .env
```

Edit `.env` with your production values:
- Set real database credentials
- Set real Redis password
- Paste JWT key contents
- Set ALLOWED_ORIGINS to your domain

5. Generate SSL certificates:
```bash
apt install certbot
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

6. Start all services:
```bash
docker compose -f docker-compose.prod.yml up -d
```

7. Run database migrations:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

8. Verify deployment:
```bash
curl https://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

## Option C: Vercel (Frontend) + Railway (Backend)

This hybrid approach gives you the best of both worlds: Vercel's edge network for the frontend and Railway's managed infrastructure for the backend.

### Frontend (Vercel)

1. Push the repo to GitHub
2. Import the project in Vercel dashboard
3. Set root directory to `frontend`
4. Set environment variable: `NEXT_PUBLIC_API_URL=https://api.vyapaarbandhu.in/api/v1`
5. Deploy

### Backend (Railway)

Follow Option A steps above for the backend only.

## Environment Variables Checklist

| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `APP_ENV` | Set to `production` | Manual |
| `DATABASE_URL` | PostgreSQL connection string | Railway auto-injects / your DB |
| `REDIS_URL` | Redis connection string | Railway auto-injects / your Redis |
| `JWT_PRIVATE_KEY` | RS256 private key PEM content | `cat keys/private.pem` |
| `JWT_PUBLIC_KEY` | RS256 public key PEM content | `cat keys/public.pem` |
| `ALLOWED_ORIGINS` | JSON array of frontend URLs | Your domain(s) |
| `WA_PHONE_NUMBER_ID` | WhatsApp Business phone ID | Meta Developer Console |
| `WA_ACCESS_TOKEN` | WhatsApp Cloud API token | Meta Developer Console |
| `WA_APP_SECRET` | WhatsApp app secret | Meta Developer Console |
| `WA_VERIFY_TOKEN` | Webhook verification token | You choose this |
| `S3_ENDPOINT_URL` | S3-compatible storage URL | Your S3/R2/MinIO |
| `S3_ACCESS_KEY_ID` | S3 access key | Your storage provider |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | Your storage provider |
| `POSTGRES_PASSWORD` | DB password (docker-compose) | You set this |
| `REDIS_PASSWORD` | Redis password (docker-compose) | You set this |

## Post-Deployment Checklist

- [ ] Health check returns 200: `curl https://your-domain/health`
- [ ] Frontend loads at root URL
- [ ] Login works (test with a registered CA account)
- [ ] WhatsApp webhook verified (Meta sends verification challenge)
- [ ] SSL certificate valid (check in browser)
- [ ] CORS headers correct (test from frontend domain)
- [ ] Rate limiting active (try 6 login attempts in 1 minute)
- [ ] Uptime monitoring configured (see `monitoring/healthcheck-config.md`)
