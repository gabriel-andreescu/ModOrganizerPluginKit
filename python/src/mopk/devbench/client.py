"""DevBench HTTP connections to a running MO2."""

from __future__ import annotations

import ipaddress
from copy import deepcopy
from datetime import UTC, datetime
from urllib.parse import urlsplit

import requests

from .errors import DevBenchError
from .instances import Instance


def _error_text(result: dict) -> str:
    texts = [
        item.get("text", "")
        for item in result.get("content", [])
        if isinstance(item, dict) and item.get("type") == "text"
    ]
    return " ".join(texts) or str(result)


class Client:
    def __init__(
        self, base_url: str, *, session: str | None = None, timeout: float = 30
    ):
        url = urlsplit(base_url)
        loopback = url.hostname == "localhost"
        if not loopback and url.hostname:
            try:
                loopback = ipaddress.ip_address(url.hostname).is_loopback
            except ValueError:
                pass
        if (
            url.scheme != "http"
            or not loopback
            or url.username
            or url.query
            or url.fragment
        ):
            raise ValueError("DevBench requires an HTTP loopback URL")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.trust_env = False
        # MO2 rejects calls carrying another process's session, so a restarted MO2
        # on the same port fails instead of receiving calls meant for the old one.
        if session:
            self.session.headers["X-Dev-Bench-Session"] = session
        self.transcript: list[dict] = []

    @classmethod
    def for_instance(cls, instance: Instance, *, timeout: float = 30) -> Client:
        return cls(instance.base_url, session=instance.session, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.session.close()

    def health(self, *, timeout: float | None = None):
        response = self.session.get(
            f"{self.base_url}/api/health",
            timeout=self.timeout if timeout is None else timeout,
        )
        response.raise_for_status()
        health = response.json()
        if not health.get("ok"):
            raise DevBenchError(f"DevBench is unhealthy: {health}")
        return health

    def tools(self) -> dict[str, dict]:
        response = self.session.get(f"{self.base_url}/api/tools", timeout=self.timeout)
        response.raise_for_status()
        return {tool["name"]: tool for tool in response.json()["tools"]}

    def call(
        self,
        tool: str,
        arguments: dict | None = None,
        *,
        record=True,
        timeout: float | None = None,
    ):
        arguments = {} if arguments is None else arguments
        receipt = {
            "time": datetime.now(UTC).isoformat(),
            "tool": tool,
            "args": deepcopy(arguments),
        }
        try:
            response = self.session.post(
                f"{self.base_url}/api/tool/{tool}",
                json=arguments,
                timeout=self.timeout if timeout is None else timeout,
            )
            if not response.ok:
                receipt["responseBody"] = response.text
                raise DevBenchError(
                    f"DevBench {tool} failed with HTTP {response.status_code}: "
                    f"{response.text}"
                )
            result = response.json()
            receipt["result"] = deepcopy(result)
            if isinstance(result, dict) and result.get("isError"):
                raise DevBenchError(f"DevBench {tool} failed: {_error_text(result)}")
            return result
        except BaseException as error:
            receipt["error"] = str(error)
            raise
        finally:
            if record or "error" in receipt:
                self.transcript.append(receipt)

    def capture(self, arguments: dict, *, timeout: float | None = None) -> dict:
        """Run the capture tool and return its structured result."""
        return self.call("capture", arguments, timeout=timeout)["structuredContent"]
