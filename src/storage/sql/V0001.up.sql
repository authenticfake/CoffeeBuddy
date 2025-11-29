BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_user_id VARCHAR(32) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_channel_id VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_offset_minutes INTEGER NOT NULL DEFAULT 5 CHECK (reminder_offset_minutes BETWEEN 1 AND 60),
    fairness_window_runs INTEGER NOT NULL DEFAULT 5 CHECK (fairness_window_runs BETWEEN 1 AND 50),
    data_retention_days INTEGER NOT NULL DEFAULT 90 CHECK (data_retention_days BETWEEN 30 AND 365),
    reminders_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_call_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_call_lead_minutes INTEGER,
    last_reset_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE RESTRICT,
    initiator_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    runner_user_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    status VARCHAR(16) NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed','canceled','failed')),
    pickup_time TIMESTAMPTZ,
    pickup_note TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    failure_reason TEXT,
    correlation_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_text TEXT NOT NULL,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    provenance VARCHAR(32) NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    canceled_at TIMESTAMPTZ,
    UNIQUE (run_id, user_id)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    last_order_text TEXT NOT NULL,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, channel_id)
);

CREATE TABLE IF NOT EXISTS runner_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    runs_served_count INTEGER NOT NULL DEFAULT 0,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, channel_id)
);

CREATE TABLE IF NOT EXISTS channel_admin_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    admin_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(32) NOT NULL CHECK (action_type IN ('enable','disable','update_config','data_reset')),
    action_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_channel_status ON runs (channel_id, status);
CREATE INDEX IF NOT EXISTS idx_runs_runner ON runs (runner_user_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_run ON orders (run_id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders (user_id);
CREATE INDEX IF NOT EXISTS idx_runner_stats_usage ON runner_stats (channel_id, runs_served_count, last_run_at);
CREATE INDEX IF NOT EXISTS idx_channel_admin_actions_channel ON channel_admin_actions (channel_id, created_at DESC);

COMMIT;