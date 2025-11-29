BEGIN;

WITH upserted_channels AS (
    INSERT INTO channels (slack_channel_id, name, reminder_offset_minutes, fairness_window_runs, data_retention_days, reminders_enabled, last_call_enabled)
    VALUES
        ('CFOCUS001', 'coffee-pilot-1', 5, 5, 90, TRUE, TRUE),
        ('CFOCUS002', 'coffee-pilot-2', 10, 5, 90, TRUE, TRUE),
        ('CFOCUS003', 'coffee-pilot-3', 5, 7, 120, TRUE, FALSE),
        ('CFOCUS004', 'coffee-pilot-4', 8, 5, 90, TRUE, TRUE),
        ('CFOCUS005', 'coffee-pilot-5', 5, 3, 60, TRUE, TRUE),
        ('CFOCUS006', 'coffee-pilot-6', 6, 4, 90, TRUE, TRUE),
        ('CFOCUS007', 'coffee-pilot-7', 4, 5, 90, TRUE, TRUE),
        ('CFOCUS008', 'coffee-pilot-8', 5, 6, 180, TRUE, TRUE),
        ('CFOCUS009', 'coffee-pilot-9', 7, 5, 90, FALSE, TRUE),
        ('CFOCUS010', 'coffee-ops',     5, 5, 90, TRUE, TRUE)
    ON CONFLICT (slack_channel_id)
    DO UPDATE
        SET name = EXCLUDED.name,
            reminder_offset_minutes = EXCLUDED.reminder_offset_minutes,
            fairness_window_runs = EXCLUDED.fairness_window_runs,
            data_retention_days = EXCLUDED.data_retention_days,
            reminders_enabled = EXCLUDED.reminders_enabled,
            last_call_enabled = EXCLUDED.last_call_enabled,
            updated_at = NOW()
    RETURNING id
)
SELECT COUNT(*) FROM upserted_channels;

COMMIT;