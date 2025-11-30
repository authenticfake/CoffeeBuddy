BEGIN;

WITH upsert_channels AS (
    INSERT INTO channels (slack_channel_id, name, reminder_offset_minutes, fairness_window_runs, data_retention_days, reminders_enabled, last_call_enabled, last_call_lead_minutes)
    VALUES
        ('CFOCUS001', 'coffee-pilot-1', 5, 5, 90, TRUE, TRUE, 5),
        ('CFOCUS002', 'coffee-pilot-2', 10, 5, 90, TRUE, TRUE, 10),
        ('CFOCUS003', 'coffee-pilot-3', 5, 7, 120, TRUE, FALSE, NULL),
        ('CFOCUS004', 'coffee-pilot-4', 8, 5, 90, TRUE, TRUE, 8),
        ('CFOCUS005', 'coffee-pilot-5', 5, 3, 60, TRUE, TRUE, 5),
        ('CFOCUS006', 'coffee-pilot-6', 6, 4, 90, TRUE, TRUE, 6),
        ('CFOCUS007', 'coffee-pilot-7', 4, 5, 90, TRUE, TRUE, 4),
        ('CFOCUS008', 'coffee-pilot-8', 5, 6, 180, TRUE, TRUE, 5),
        ('CFOCUS009', 'coffee-pilot-9', 7, 5, 90, FALSE, TRUE, 7),
        ('CFOCUS010', 'coffee-ops',     5, 5, 90, TRUE, TRUE, 5)
    ON CONFLICT (slack_channel_id) DO UPDATE
    SET name = EXCLUDED.name,
        reminder_offset_minutes = EXCLUDED.reminder_offset_minutes,
        fairness_window_runs = EXCLUDED.fairness_window_runs,
        data_retention_days = EXCLUDED.data_retention_days,
        reminders_enabled = EXCLUDED.reminders_enabled,
        last_call_enabled = EXCLUDED.last_call_enabled,
        last_call_lead_minutes = EXCLUDED.last_call_lead_minutes
    RETURNING id, slack_channel_id
)
SELECT COUNT(*) FROM upsert_channels;

COMMIT;