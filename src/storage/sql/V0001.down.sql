BEGIN;

DROP INDEX IF EXISTS idx_channel_admin_actions_channel;
DROP INDEX IF EXISTS idx_runner_stats_usage;
DROP INDEX IF EXISTS idx_orders_user;
DROP INDEX IF EXISTS idx_orders_run;
DROP INDEX IF EXISTS idx_runs_runner;
DROP INDEX IF EXISTS idx_runs_channel_status;

DROP TABLE IF EXISTS channel_admin_actions CASCADE;
DROP TABLE IF EXISTS runner_stats CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS runs CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS users CASCADE;

COMMIT;