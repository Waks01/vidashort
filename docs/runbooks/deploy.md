# Deploy Runbook

## Pre-flight

- [ ] All tests pass: `cd apps/api && pytest tests/ -q`
- [ ] No TypeScript errors: `cd mobile && npx tsc --noEmit`
- [ ] `main` is green on CI
- [ ] Changelog updated

## Steps

```bash
cd apps/api
fly deploy
```

## Post-deploy

```bash
curl -fsS https://api.vidashort.app/health
fly logs --app vidashort-api-prod | grep -i error | tail -20
```

## Mobile

```bash
cd mobile
eas build --platform all --profile production
```

## Rollback

See `rollback.md`.
