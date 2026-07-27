# Runbook — OneDrive exclusion (Windows)

The `apps/mobile/` and future `apps/api/` directories will get heavy folders that must NOT sync to OneDrive. If you don't exclude them, your laptop fans will scream and sync will take hours.

## Why this is needed

- `apps/mobile/node_modules/` — ~ 600 MB, regenerable with `npm install`.
- `apps/mobile/.expo/` — ~ 50 MB, regenerable.
- `apps/api/.venv/` — ~ 200 MB, regenerable with `uv sync`.
- `apps/api/__pycache__/` — regenerable.
- `apps/api/.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` — regenerable.

None of these need to be on OneDrive. They're reproducible from `package.json`, `package-lock.json`, `pyproject.toml`, `uv.lock`.

## What to exclude

Open the OneDrive system tray icon → ⚙ Settings → Sync and backup → Advanced settings.

Click "Manage backup" (or "Choose folders" in older versions).

Under the `vidashort` folder, **uncheck** these subfolders:
- `apps\mobile\node_modules`
- `apps\mobile\.expo`
- `apps\mobile\dist`
- `apps\api\.venv`
- `apps\api\__pycache__`
- `apps\api\.pytest_cache`
- `apps\api\.mypy_cache`
- `apps\api\.ruff_cache`

If a subfolder doesn't exist yet, OneDrive will silently ignore it. Add the exclusion now, future folders will be excluded automatically.

## Alternative: .gitignore + OneDrive Files On-Demand

If you have Files On-Demand enabled (default for most personal OneDrive accounts), OneDrive won't download files until you open them. Combined with `.gitignore`, this is enough.

To enable Files On-Demand:
- OneDrive icon → ⚙ Settings → Sync and backup → Advanced settings → "Files On-Demand" → On.

To verify:
- Open File Explorer. The excluded folders should show a cloud icon (☁️) and 0 bytes locally.
- The `vidashort/apps/mobile/node_modules` folder, for example, should be a stub that downloads on demand.

## How to verify the exclusion works

```bash
# After running `npm install` in apps/mobile
du -sh apps/mobile/node_modules  # Mac/Linux
# OR
# Right-click the folder in File Explorer → Properties → Size

# Then look at the OneDrive icon. If sync is paused for that folder, you're good.
```

## What happens if you forget

Your laptop fans will run at 100%. The sync will take hours. Your battery will die.

If this happens:
1. Pause OneDrive sync immediately (system tray icon → Pause syncing).
2. Add the exclusions.
3. Resume sync.
4. Run `npm ci` in `apps/mobile/` to regenerate `node_modules` (faster than sync).

## Why we don't script this

The OneDrive exclusion UI is the only way to set this, and it requires user interaction. There's no CLI for it. We considered PowerShell + registry hack but it's brittle across OneDrive versions. The user does this once per machine.

## Path note

`C:\Users\kenik\OneDrive\Pictures\vidashort\` is the current root. If you move the repo, re-do the exclusions at the new path.
