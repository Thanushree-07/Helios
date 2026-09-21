from prometheus_client import Counter, Histogram

# Total requests, broken down by outcome
REQUEST_COUNT = Counter(
    "helios_requests_total",
    "Total number of /chat requests",
    ["cache_result", "provider"],
)


# How many times each provider failed
PROVIDER_FAILURES = Counter(
    "helios_provider_failures_total",
    "Total provider call failures",
    ["provider"],
)

REQUEST_LATENCY = Histogram(
    "helios_request_latency_seconds",
    "Latency of /chat requests in seconds",
    ["cache_result"],
)