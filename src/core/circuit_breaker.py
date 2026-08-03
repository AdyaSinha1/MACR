import time
from structlog import get_logger

logger = get_logger()


class CircuitBreakerOpenException(Exception):
    """Exception raised when the circuit breaker is open."""


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        """
        Args:
            failure_threshold: Number of failures before the circuit opens.
            recovery_timeout: Time in seconds before a HALF_OPEN state is attempted.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_failure(self):
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            self.failures = self.failure_threshold
            logger.warning(
                "Circuit reopened after failure in half-open state.")
        else:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(
                    "Circuit breaker opened due to repeated failures.")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def is_allowed(self) -> bool:
        """Check if execution is allowed based on the circuit breaker state."""
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker half-open. Attempting recovery.")
                return True
            return False

        if self.state == "HALF_OPEN":
            return True

        return True
