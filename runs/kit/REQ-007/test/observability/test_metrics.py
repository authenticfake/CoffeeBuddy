from coffeebuddy.observability.metrics import build_metrics_suite


def test_metrics_suite_counts_requests_and_runs() -> None:
    suite = build_metrics_suite()

    suite.request.observe("slash", 200, 0.2)
    suite.request.observe("slash", 400, 0.4)
    suite.request.observe("slash", 503, 0.8)

    ok_value = suite.registry.get_sample_value(
        "coffeebuddy_requests_total", labels={"type": "slash", "result": "ok"}
    )
    client_err_value = suite.registry.get_sample_value(
        "coffeebuddy_requests_total", labels={"type": "slash", "result": "client_error"}
    )
    error_value = suite.registry.get_sample_value(
        "coffeebuddy_requests_total", labels={"type": "slash", "result": "error"}
    )

    assert ok_value == 1.0
    assert client_err_value == 1.0
    assert error_value == 1.0

    suite.runs.record("started")
    suite.runs.record("closed", duration_seconds=120.0)

    run_started = suite.registry.get_sample_value(
        "coffeebuddy_runs_total", labels={"status": "started"}
    )
    run_closed = suite.registry.get_sample_value(
        "coffeebuddy_runs_total", labels={"status": "closed"}
    )
    duration_sum = suite.registry.get_sample_value(
        "coffeebuddy_run_duration_seconds_sum", labels={"status": "closed"}
    )

    assert run_started == 1.0
    assert run_closed == 1.0
    assert duration_sum == 120.0