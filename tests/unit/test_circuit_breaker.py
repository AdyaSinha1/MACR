import time
from core.circuit_breaker import CircuitBreaker


def test_circuit_breaker_state_transitions():
    """Tests the complete CLOSED -> OPEN -> HALF_OPEN -> CLOSED state machine."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

    # 1. Initial state is CLOSED and allows execution
    assert cb.state == "CLOSED"
    assert cb.is_allowed() is True

    # 2. Accumulate failures to open the circuit
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.is_allowed() is False

    # 3. Wait for recovery_timeout -> transitions to HALF_OPEN
    time.sleep(0.15)
    assert cb.is_allowed() is True
    assert cb.state == "HALF_OPEN"

    # 4. A success in HALF_OPEN fully closes the circuit
    cb.record_success()
    assert cb.state == "CLOSED"

    # 5. Re-open circuit via failures
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "OPEN"

    # 6. Wait for recovery again -> HALF_OPEN
    time.sleep(0.15)
    cb.is_allowed()
    assert cb.state == "HALF_OPEN"

    # 7. A single failure in HALF_OPEN immediately reopens the circuit
    cb.record_failure()
    assert cb.state == "OPEN"
