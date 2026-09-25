import time

from app.resilience.circuit_breaker import CircuitBreaker, CircuitState


def test_starts_closed():
    breaker = CircuitBreaker("test-provider")
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_opens_after_threshold_failures():
    breaker = CircuitBreaker("test-provider")

    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED  # only 2 failures, still under threshold

    breaker.record_failure()  # 3rd failure hits FAILURE_THRESHOLD
    assert breaker.state == CircuitState.OPEN


def test_blocks_requests_while_open():
    breaker = CircuitBreaker("test-provider")
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False  # cooldown hasn't elapsed yet


def test_moves_to_half_open_after_cooldown():
    breaker = CircuitBreaker("test-provider")
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    # simulate time passing by manually rewinding "opened_at"
    breaker.opened_at = time.time() - breaker.COOLDOWN_SECONDS - 1

    assert breaker.allow_request() is True
    assert breaker.state == CircuitState.HALF_OPEN


def test_success_resets_to_closed():
    breaker = CircuitBreaker("test-provider")
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()
    breaker.opened_at = time.time() - breaker.COOLDOWN_SECONDS - 1
    breaker.allow_request()  # moves to HALF_OPEN

    breaker.record_success()

    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_failure_during_half_open_reopens():
    breaker = CircuitBreaker("test-provider")
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()
    breaker.opened_at = time.time() - breaker.COOLDOWN_SECONDS - 1
    breaker.allow_request()  # moves to HALF_OPEN

    breaker.record_failure()  # the test request failed

    assert breaker.state == CircuitState.OPEN