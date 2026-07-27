# Runbook — debugging a bug

When something's broken, here's how to find it.

## Step 0: confirm it's a bug

- Did the user report it? Or did you find it? Either way, write down the exact symptoms first.
- Can you reproduce it? If not, ask the user for more detail (steps, what they expected, what happened).

## Step 1: read the symptom

Common shapes:

- "Screen is blank" → probably a runtime error. Check the console / logs.
- "Button does nothing" → click handler missing or wrong.
- "Wrong data showing" → mock vs real mismatch, or schema drift.
- "Crash on launch" → most likely a missing import, a renamed export, or a hot-reload artifact.
- "Works on iOS, broken on Android" → platform-specific. Check expo-video, haptics, gesture handler.
- "Works locally, broken in prod" → env vars, CORS, missing migration.

## Step 2: locate the error

### Mobile

```bash
# In the Expo dev tools:
# - Open the JS debugger
# - Check the Metro log for stack traces
# - Open React DevTools for component state

# In the iOS Simulator:
# - Cmd+D → Debug Remote JS
# - Cmd+D → Open React DevTools

# In the Android Emulator:
# - Cmd+M → Debug
# - Open the Logcat in Android Studio
```

Look for:
- `console.error` (red) — your problem
- `console.warn` (yellow) — maybe your problem
- Unhandled promise rejection — your problem
- Native crash log — likely an SDK issue, check Expo SDK 57 compat

### Backend

```bash
# uvicorn log shows the request and the response
# Sentry captures unhandled exceptions

# Check the local DB
psql $DATABASE_URL
# \dt to list tables
# SELECT * FROM users WHERE id = '...'; to inspect
```

Look for:
- 5xx → Sentry has the stack trace
- 4xx → expected for client errors, not bugs
- Slow query → check `pg_stat_statements`

## Step 3: read the code

- Read the file the error points to.
- Read the 2 files that import it.
- If the error is in a service, read the schema and the test.
- If the error is in a route, read the schema and the service.

## Step 4: form a hypothesis, then test

Don't change 5 things at once. Form a hypothesis, change one thing, verify, repeat.

```bash
# Hypothesis: the data shape from /v1/me doesn't include the field the UI is reading.
# Test: log the response in the API client, log the field the UI is reading.
# Confirm or refute.
```

## Step 5: fix

- Make the smallest change that fixes it.
- Don't refactor while fixing. The fix and the refactor are two PRs.
- If the fix is non-obvious, add a comment.
- If the fix changes a contract, update the docs in the same commit.

## Step 6: prevent the regression

- **Visual prototype:** add a smoke-test HTML page that exercises the path. (Phase 1+ work, not now.)
- **Mobile:** add a unit test for the lib function, or an integration test for the hook.
- **Backend:** add a pytest case. If the bug is in the paywall, the test goes in `test_entitlement.py`. Always.

## Step 7: verify the fix

- Run the original repro steps.
- Run any test that covers this area.
- Re-run the phase verification if the fix could affect adjacent flows.

## Common bug patterns in this codebase

### "MockData is undefined" in the prototype

The `data.js` script must load before `app.js`. If you see this, check the script tags in the HTML.

### "Cannot read property X of undefined" in the mobile app

Schema drift. The API changed, the client didn't. Check `packages/shared/src/schemas/` and the API contract.

### "Hydration mismatch" in the mobile app

Server-rendered output differs from client. With expo-router this is rare; usually a token-storage issue. Check `lib/auth/storage.ts`.

### "401 Unauthorized" in a loop

The refresh token is being rotated but the secure-store isn't being updated. Check `lib/auth/provider.tsx`.

### "Cap reached" but the user only watched 1 ad

The Redis cap counter is from a different day, or the test data has wrong UTC dates. Check `services/ad_cap.py → today_key()`.

### Creator earnings don't match the expected 60%

A rounding error in `services/revenue_split.py`. Always use integer math: `gross * 60 // 100`, not `gross * 0.6`.

## If you can't find it in 30 minutes

Stop. Ask the user. The bug is probably in a place neither of us has looked yet. Describe what you've checked. Let the user point.

## If you find a bug, document it

If the bug is non-trivial (took you more than 10 minutes to find), write a sentence in `docs/runbooks/known-issues.md` (Phase 1+) so the next agent doesn't repeat the same search.
