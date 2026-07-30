# Rollback Runbook

## API Rollback

```bash
cd apps/api
fly deploy --version <last_known_good_image>
```

Verify:
```bash
curl -fsS https://api.vidashort.app/health
```

## Mobile Rollback

In App Store Connect / Play Console:
1. Halt phased rollout
2. Revert to previous build
3. Submit hotfix if needed

## Database Rollback

Never rollback migrations in production.
Instead, forward-fix with a new migration.

## Cache Purge

If bad code served cached responses:
```bash
# Cloudflare purge through dashboard or API
curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE/purge_cache" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}'
```
