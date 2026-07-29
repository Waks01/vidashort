# Runbook — EAS development builds

EAS (Expo Application Services) builds your APK in the cloud, so you don't need a local JDK or Android Studio. This is the path for installing a real native build on a phone for QA.

## Prerequisites

1. An Expo account: <https://expo.dev/signup> (free, GitHub OAuth)
2. The `eas` CLI: already installed locally (`eas-cli/21.3.0`). If missing: `npm i -g eas-cli`
3. Your project linked to your Expo account: `cd mobile && npx eas init` (one-time, interactive — creates the project on Expo's side)
4. **No local JDK required.** EAS build servers have JDK 17 + the Android SDK + Gradle pre-installed.

## Build profiles

`mobile/eas.json` defines three profiles:

| Profile | What it does | Use for |
|---|---|---|
| `development` | Builds a debug APK with the dev client enabled (`expo-dev-client`). Internal distribution — installs via a one-time URL. | Testing on your own phone, day-to-day dev |
| `preview` | Internal distribution, release build, no dev client. | Sharing pre-release builds with internal testers |
| `production` | App-bundle (`.aab`), production channel. | Submitting to Google Play |

## How to trigger a build

```bash
cd mobile

# First time only: link this repo to your Expo account
npx eas init
# → choose: scope = your username, name = vidashort, platform = android

# Build the dev client APK
npx eas build -p android --profile development
# → uploads source to Expo, runs gradle in the cloud, gives you a download URL in ~5-10 min

# Same for preview
npx eas build -p android --profile preview

# Production (creates .aab for Play Store)
npx eas build -p android --profile production
```

After the build finishes, `eas build` prints a URL. Open it on your Android phone (or `adb install <url>` if you have the SDK). The dev-client APK has the Expo dev menu — you can shake-to-reload, point it at any backend URL, etc.

## What the build server does

For `profile: development`, the EAS server:

1. Runs `expo prebuild` (no-op if `android/` is already committed — which it is, after we ran `expo prebuild --clean`)
2. Sets up JDK 17 + Android SDK + Gradle in a clean container
3. Runs `:app:assembleDebug` (per `eas.json` android.gradleCommand)
4. Signs the APK with an auto-generated dev keystore
5. Uploads the artifact to EAS storage and gives you a download URL

## Local vs cloud: which to use when

| Goal | Path |
|---|---|
| Quick UI iteration, no native module changes | `npx expo start` (dev server, no native build). Works in Expo Go for the bare-bones JS side. |
| Native module changed (reanimated, applovin, etc.), want to test on device | EAS `development` build |
| Show internal team a release-quality build | EAS `preview` build |
| Submit to Play Store | EAS `production` build, then `eas submit -p android` |

## Common gotchas

- **First build is slow** (~5-10 min) because it has to install all gradle deps. Subsequent builds cache and finish in ~2 min.
- **Signing**: EAS manages keystores for you. You don't need to generate one locally. For local debug builds (if you ever go that route), Expo ships `android/app/debug.keystore` automatically.
- **Channel**: every build profile has a `channel`. OTA updates via `eas update --branch <channel>` ship to that channel only. We don't have updates set up yet — that's a Phase 4 concern.
- **Per-project cost**: Expo's free tier gives you 30 cloud builds/month + 1,000 OTA updates/month. Plenty for dev.
- **Public visibility**: `distribution: "internal"` means the download URL is unguessable but technically anyone with the link can install. For closed betas with NDA users, use `internal` + a private channel; for true "invite-only", use `eas build --distribution simulator-store` or push to TestFlight / Play Internal Testing.

## What's NOT in `eas.json`

- `submit.production` for Android points at the default Google Play track. To actually submit, you need:
  1. A Google Play Console account ($25 one-time)
  2. A service account JSON (`google-services.json` + service-account key) uploaded via `eas credentials`
- iOS submission: needs Apple Developer account ($99/yr) + App Store Connect API key. Skip until Phase 5.
