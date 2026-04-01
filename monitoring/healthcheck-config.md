# Uptime Monitoring Setup

## Option A: UptimeRobot (Recommended -- Free Tier)

UptimeRobot provides 50 monitors with 5-minute check intervals on the free tier.

### Setup Steps

1. Create an account at [https://uptimerobot.com](https://uptimerobot.com)

2. Click "Add New Monitor"

3. Configure the monitor:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: VyapaarBandhu Health
   - **URL**: `https://your-domain.com/health`
   - **Monitoring Interval**: 5 minutes

4. Configure alert contacts:
   - Add your email address
   - Optionally add a Slack webhook or Telegram bot

5. Set alert conditions:
   - **Alert when**: Response status is not 200
   - **Alert after**: 2 consecutive failures (to avoid false positives)

6. Add a second monitor for the API:
   - **URL**: `https://your-domain.com/health/ready`
   - This catches database or Redis outages specifically

### Recommended Monitors

| Monitor | URL | Interval | Alert Threshold |
|---------|-----|----------|-----------------|
| Health Check | `/health` | 5 min | 2 failures |
| Readiness | `/health/ready` | 5 min | 2 failures |
| Frontend | `/` | 5 min | 3 failures |
| API Root | `/api/v1/` | 5 min | 2 failures |

## Option B: Better Stack (Alternative -- Free Tier)

Better Stack (formerly Better Uptime) offers a better UI with incident management.

### Setup Steps

1. Create account at [https://betterstack.com](https://betterstack.com)
2. Go to Monitors > Create Monitor
3. Set URL to `https://your-domain.com/health`
4. Set check period to 3 minutes (free tier allows this)
5. Configure email + optional Slack notifications
6. Create a status page for transparency

## Grafana Cloud (Metrics Dashboard)

1. Sign up at [https://grafana.com/products/cloud/](https://grafana.com/products/cloud/)
   - Free tier: 10,000 series, 14 days retention
2. Add Prometheus data source pointing to your `/metrics` endpoint
3. Import the dashboard from `monitoring/grafana-dashboard.json`
   - Go to Dashboards > Import > Upload JSON
4. Set refresh interval to 30 seconds
