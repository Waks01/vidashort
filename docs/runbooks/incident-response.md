# Incident Response Runbook

## Severity Levels

- **P0** — API down or 5xx > 5%. Mobile crashes > 1%. Money flow broken.
- **P1** — Degraded performance. Major feature broken for a segment.
- **P2** — Minor bug. Workaround available.
- **P3** — Cosmetic. No user impact.

## On-Call Checklist

1. Check health: `curl -fsS https://api.vidashort.app/health`
2. Check Sentry: look for spikes in errors
3. Check PostHog: funnels dropping
4. Check Fly: `fly status vidashort-api-prod`
5. Check Redis: `fly ssh console -C "redis-cli ping"`

## Rollback

```bash
cd apps/api
fly deploy --version <last_known_good>
```

## Communication

- Post status to #incidents Slack channel
- Update status page if P0 or P1
