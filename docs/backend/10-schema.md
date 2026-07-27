# Database schema

The 14 tables. Postgres 16 (Neon). Source of truth lives in `apps/api/alembic/versions/`.

## Why Postgres, not MongoDB

- We need **ACID** for money. `users.coins` and `coin_txn.delta` must be consistent.
- We need **joins** (series → episodes → comments, users → favorites → series).
- We need **transactions** (the paywall debit is one transaction across `users`, `coin_txn`, `creator_earnings`).
- Redis is the right tool for the cap counter. Postgres is the right tool for everything else.

## Convention

- All tables: `id` is `uuid` (use `uuid_generate_v4()` or Python's `uuid.uuid4()`).
- All timestamps: `timestamptz` (timezone-aware). Default `now()`.
- All foreign keys: `ON DELETE` explicit. Soft-delete only on `users`.
- All enums: `pg_enum` with the values spelled out.
- Money: integer `coins`. Naira only as display.

## Tables

### users
```sql
CREATE TABLE users (
  id                uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email             citext UNIQUE NOT NULL,
  name              text NOT NULL,
  role              user_role NOT NULL DEFAULT 'viewer',  -- 'viewer' | 'creator' | 'admin'
  avatar_url        text,
  coins             integer NOT NULL DEFAULT 0 CHECK (coins >= 0),
  loyalty_coins     integer NOT NULL DEFAULT 0 CHECK (loyalty_coins >= 0),
  genres            text[] NOT NULL DEFAULT '{}',
  language          text NOT NULL DEFAULT 'en',
  age_confirmed     boolean NOT NULL DEFAULT false,
  onboarded         boolean NOT NULL DEFAULT false,
  banned_at         timestamptz,
  ban_reason        text,
  deleted_at        timestamptz,           -- soft delete (30-day restore window)
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE user_role AS ENUM ('viewer', 'creator', 'admin');

CREATE INDEX idx_users_role ON users(role) WHERE role != 'viewer';
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
```

`coins` is the **wallet balance** (spendable). `loyalty_coins` is the **creator earnings balance** (only withdrawable after ₦5,000). These are separate so a creator can't accidentally spend their earnings on an unlock.

### user_identities
```sql
CREATE TABLE user_identities (
  id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id             uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider            identity_provider NOT NULL,  -- 'email' | 'apple' | 'google'
  provider_user_id    text NOT NULL,               -- Apple sub, Google sub, or email
  password_hash       text,                        -- bcrypt, only for provider='email'
  last_login_at       timestamptz,
  created_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider, provider_user_id)
);

CREATE TYPE identity_provider AS ENUM ('email', 'apple', 'google');
```

### refresh_tokens
```sql
CREATE TABLE refresh_tokens (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash      text NOT NULL UNIQUE,        -- sha256 of the raw token
  used_at         timestamptz,                -- for rotation
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  user_agent      text,
  ip              inet
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

### password_resets
```sql
CREATE TABLE password_resets (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash      text NOT NULL UNIQUE,
  expires_at      timestamptz NOT NULL,
  used_at         timestamptz,
  created_at      timestamptz NOT NULL DEFAULT now()
);
```

### series
```sql
CREATE TABLE series (
  id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  slug                text UNIQUE NOT NULL,
  title               text NOT NULL,
  synopsis            text NOT NULL,
  cover_url           text NOT NULL,
  backdrop_url        text,
  category            text NOT NULL,            -- genre from MockData.genres
  language            text NOT NULL DEFAULT 'en',
  source              series_source NOT NULL,  -- 'original' | 'tmdb' | 'creator'
  creator_id          uuid REFERENCES users(id) ON DELETE SET NULL,  -- null for originals + TMDB
  copyright_owner     text,
  is_published        boolean NOT NULL DEFAULT false,
  is_vip_only         boolean NOT NULL DEFAULT false,
  free_episodes       integer NOT NULL DEFAULT 3,  -- first N free
  moderation_status   moderation_status NOT NULL DEFAULT 'draft',  -- 'draft' | 'pending' | 'approved' | 'rejected'
  allowed_countries   text[],                  -- null = all
  tags                text[] NOT NULL DEFAULT '{}',
  tmdb_id             text,
  total_episodes      integer NOT NULL DEFAULT 0,
  rating              numeric(3,2) NOT NULL DEFAULT 0,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE series_source AS ENUM ('original', 'tmdb', 'creator');
CREATE TYPE moderation_status AS ENUM ('draft', 'pending', 'approved', 'rejected');

CREATE INDEX idx_series_published ON series(is_published, total_episodes DESC) WHERE is_published = true;
CREATE INDEX idx_series_category ON series(category) WHERE is_published = true;
CREATE INDEX idx_series_creator ON series(creator_id);
CREATE INDEX idx_series_pending ON series(moderation_status) WHERE moderation_status = 'pending';
```

### episodes
```sql
CREATE TABLE episodes (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  series_id       uuid NOT NULL REFERENCES series(id) ON DELETE CASCADE,
  number          integer NOT NULL,
  title           text NOT NULL,
  synopsis        text,
  duration_s      integer NOT NULL,
  video_uid       text,                       -- Cloudflare Stream UID
  video_ready     boolean NOT NULL DEFAULT false,
  required_coins  integer NOT NULL DEFAULT 25,
  is_free         boolean NOT NULL DEFAULT false,
  ad_preroll      boolean NOT NULL DEFAULT true,
  ad_midroll_at_s integer,                    -- null = no midroll
  thumbnail_url   text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (series_id, number)
);

CREATE INDEX idx_episodes_series ON episodes(series_id, number);
```

### watch_history
```sql
CREATE TABLE watch_history (
  id                    uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id               uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  episode_id            uuid NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  position_s            integer NOT NULL DEFAULT 0,
  completed             boolean NOT NULL DEFAULT false,
  unlocked_via_coins    boolean NOT NULL DEFAULT false,
  unlocked_via_ad       boolean NOT NULL DEFAULT false,
  unlocked_via_vip      boolean NOT NULL DEFAULT false,
  watched_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_watch_history_resume ON watch_history(user_id, episode_id, watched_at DESC);
CREATE INDEX idx_watch_history_user ON watch_history(user_id, watched_at DESC);
```

### favorites
```sql
CREATE TABLE favorites (
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  series_id   uuid NOT NULL REFERENCES series(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, series_id)
);
```

### comments
```sql
CREATE TABLE comments (
  id            uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  episode_id    uuid NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  user_id       uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  parent_id     uuid REFERENCES comments(id) ON DELETE CASCADE,  -- replies
  body          text NOT NULL,
  likes         integer NOT NULL DEFAULT 0,
  deleted_at    timestamptz,  -- soft delete
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_comments_episode ON comments(episode_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_user ON comments(user_id) WHERE deleted_at IS NULL;
```

### coin_txn (the ledger — append-only)
```sql
CREATE TABLE coin_txn (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  delta           integer NOT NULL,                  -- +credit, -debit
  reason          coin_txn_reason NOT NULL,           -- 'purchase' | 'rewarded_ad' | 'unlock' | 'refund' | 'daily' | 'admin' | 'restore'
  ref_id          uuid,                                -- polymorphic (episode_id, pack_id, etc.)
  balance_after   integer NOT NULL,
  idempotency_key text UNIQUE,                        -- for IAP receipts
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE coin_txn_reason AS ENUM (
  'purchase', 'rewarded_ad', 'unlock', 'refund',
  'daily_reward', 'admin_grant', 'admin_refund', 'restore'
);

CREATE INDEX idx_coin_txn_user ON coin_txn(user_id, created_at DESC);
```

**Why append-only:** We never UPDATE or DELETE rows in `coin_txn`. Refunds add a negative row. This makes the money trail auditable forever and makes reconciliation trivial.

### creator_earnings
```sql
CREATE TABLE creator_earnings (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  creator_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  episode_id      uuid NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  gross_coins     integer NOT NULL,             -- 25 for one unlock
  creator_coins   integer NOT NULL,             -- 15 (60% of 25)
  created_at      timestamptz NOT NULL DEFAULT now(),
  -- Used to compute creator's pending balance:
  -- pending = SUM(creator_coins) - SUM(payout_requests.amount_coins WHERE status IN ('approved', 'paid'))
  UNIQUE (creator_id, episode_id, created_at)   -- same user can't unlock same ep twice → no double-credit
);

CREATE INDEX idx_creator_earnings_creator ON creator_earnings(creator_id, created_at DESC);
```

### payout_requests
```sql
CREATE TABLE payout_requests (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  creator_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount_coins    integer NOT NULL,
  amount_naira    numeric(10,2) NOT NULL,         -- display only
  status          payout_status NOT NULL DEFAULT 'pending',
  payout_method   payout_method NOT NULL,         -- 'OPay' | 'PalmPay' | 'Moniepoint' | 'Bank'
  payout_account  text NOT NULL,
  requested_at    timestamptz NOT NULL DEFAULT now(),
  decided_at      timestamptz,
  decided_by      uuid REFERENCES users(id),
  note            text
);

CREATE TYPE payout_status AS ENUM ('pending', 'approved', 'rejected', 'paid', 'cancelled');
CREATE TYPE payout_method AS ENUM ('OPay', 'PalmPay', 'Moniepoint', 'Bank');

CREATE INDEX idx_payout_requests_creator ON payout_requests(creator_id, requested_at DESC);
CREATE INDEX idx_payout_requests_status ON payout_requests(status, requested_at);
```

### ad_impressions
```sql
CREATE TABLE ad_impressions (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ad_id           text NOT NULL,                 -- AppLovin ad unit ID
  ad_network      text NOT NULL DEFAULT 'appLovin',
  ad_type         ad_type NOT NULL,              -- 'rewarded' | 'interstitial'
  watched_s       integer NOT NULL,
  completed       boolean NOT NULL,
  rewarded_coins  integer NOT NULL DEFAULT 0,
  country         text,
  app_version     text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, ad_id)                        -- same ad can't credit twice
);

CREATE TYPE ad_type AS ENUM ('rewarded', 'interstitial');

CREATE INDEX idx_ad_impressions_user_daily ON ad_impressions(user_id, created_at::date);
CREATE INDEX idx_ad_impressions_type ON ad_impressions(ad_type, created_at DESC);
```

### vip_entitlements
```sql
CREATE TABLE vip_entitlements (
  id                    uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id               uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  source                vip_source NOT NULL,    -- 'apple' | 'google' | 'revenuecat' | 'manual'
  product_id            text NOT NULL,           -- 'vip_weekly' | 'vip_monthly' | 'vip_yearly'
  started_at            timestamptz NOT NULL,
  expires_at            timestamptz NOT NULL,
  auto_renew            boolean NOT NULL DEFAULT true,
  original_txn_id       text,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE vip_source AS ENUM ('apple', 'google', 'revenuecat', 'manual');

CREATE INDEX idx_vip_entitlements_user_active ON vip_entitlements(user_id, expires_at DESC);
```

### moderation_items
```sql
CREATE TABLE moderation_items (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  kind            moderation_kind NOT NULL,     -- 'series' | 'comment' | 'account'
  ref_id          uuid NOT NULL,
  submitter_id    uuid REFERENCES users(id),
  reason          text NOT NULL,                -- human-readable, e.g. "Auto-flagged: contains banned word"
  status          moderation_item_status NOT NULL DEFAULT 'pending',
  auto_flagged    boolean NOT NULL DEFAULT false,
  decided_at      timestamptz,
  decided_by      uuid REFERENCES users(id),
  note            text,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TYPE moderation_kind AS ENUM ('series', 'comment', 'account');
CREATE TYPE moderation_item_status AS ENUM ('pending', 'approved', 'rejected');

CREATE INDEX idx_moderation_pending ON moderation_items(kind, status, created_at) WHERE status = 'pending';
```

### audit_log
```sql
CREATE TABLE audit_log (
  id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  actor_id        uuid NOT NULL REFERENCES users(id),
  action          text NOT NULL,                -- 'moderation.decide' | 'user.ban' | ...
  target_kind     text NOT NULL,                -- 'series' | 'user' | 'payout' | ...
  target_id       uuid NOT NULL,
  before          jsonb,                        -- full snapshot before
  after           jsonb,                        -- full snapshot after
  ip              inet,
  user_agent      text,
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_actor ON audit_log(actor_id, created_at DESC);
CREATE INDEX idx_audit_log_target ON audit_log(target_kind, target_id, created_at DESC);
```

We never DELETE rows from `audit_log`. It's append-only.

## Materialized views (Phase 4)

For admin dashboard perf:

```sql
CREATE MATERIALIZED VIEW mv_daily_kpis AS
SELECT
  date_trunc('day', created_at) AS day,
  COUNT(DISTINCT user_id) AS dau,
  COUNT(*) AS events
FROM watch_history
WHERE created_at > now() - interval '90 days'
GROUP BY 1;

-- Refresh every 15 min via cron
```

## Migrations

- One file per migration, numbered `0001_initial.py`, `0002_add_*.py`, etc.
- Each migration is reversible (Alembic autogenerate + hand-fix).
- **Never** edit a committed migration. Add a new one.
- Migration names describe the change: `add_vip_entitlements`, `index_coin_txn_user_daily`.
- For destructive changes: 3 migrations (add new column → backfill → drop old).

## Why we use `citext` for email

Case-insensitive without app-side `lower()`. Postgres extension. Indexable. Same cost as text.

## Why `timestamptz` not `timestamp`

All timestamps in UTC. The client renders in local time. Storing with `timestamp` (no tz) loses information; `timestamptz` doesn't.

## Why we never `DELETE` from `coin_txn`

The ledger is the financial record. Refunds are negative rows. Adjustments are zero-sum pairs. This is the only way to be auditable to investors / tax authorities / ourselves in 2 years.
