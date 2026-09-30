"""Polling for tests."""

import json
import time


def wait_for(
    read,
    predicate=bool,
    message="Condition did not become true",
    *,
    timeout=10,
    interval=0.05,
):
    deadline = time.monotonic() + timeout
    while True:
        observed = read()
        if predicate(observed):
            return observed
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"{message}. Last state: {json.dumps(observed, default=str)}"
            )
        time.sleep(interval)
