import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"        # normal — requests flow through
    OPEN = "open"            # broken — requests are blocked
    HALF_OPEN = "half_open"  # testing — let one request through to check recovery


class CircuitBreaker:
    """
    One circuit breaker per provider. Tracks consecutive failures and
    temporarily stops sending traffic to a provider that's clearly down,
    instead of hammering it with every incoming request.
    """

    FAILURE_THRESHOLD = 3
    COOLDOWN_SECONDS = 30

    def __init__(self, name: str):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at: float | None = None

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.opened_at >= self.COOLDOWN_SECONDS:
                print(f"[circuit_breaker:{self.name}] cooldown elapsed, moving to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        # HALF_OPEN: allow exactly one test request through
        return True

    def record_success(self) -> None:
        if self.state != CircuitState.CLOSED:
            print(f"[circuit_breaker:{self.name}] recovered, closing circuit")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self) -> None:
        self.failure_count += 1
        print(f"[circuit_breaker:{self.name}] failure #{self.failure_count}")

        if self.state == CircuitState.HALF_OPEN:
            print(f"[circuit_breaker:{self.name}] test request failed, reopening")
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            return

        if self.failure_count >= self.FAILURE_THRESHOLD:
            print(f"[circuit_breaker:{self.name}] threshold reached, opening circuit")
            self.state = CircuitState.OPEN
            self.opened_at = time.time()


class CircuitBreakerRegistry:
    """Keeps one CircuitBreaker instance per provider name, shared across requests."""

    _breakers: dict[str, CircuitBreaker] = {}

    @classmethod
    def get(cls, provider_name: str) -> CircuitBreaker:
        if provider_name not in cls._breakers:
            cls._breakers[provider_name] = CircuitBreaker(provider_name)
        return cls._breakers[provider_name]