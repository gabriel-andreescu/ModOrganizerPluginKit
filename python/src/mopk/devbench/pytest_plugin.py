"""Load explicitly with pytest_plugins = ['mopk.devbench.pytest_plugin']."""

import json
import re
from contextlib import contextmanager
from functools import partial
from pathlib import Path

import pytest
import requests

from mopk.testing import wait_for

from .client import Client
from .errors import DevBenchError
from .instances import find_instance
from .visual import Visual


def pytest_addoption(parser):
    group = parser.getgroup("devbench")
    group.addoption(
        "--mo2-tests",
        action="store_true",
        help="Enable tests that control a running MO2",
    )
    group.addoption("--devbench-url", help="HTTP address of the intended DevBench host")
    group.addoption("--devbench-install", help="MO2 install directory to select")
    group.addoption("--devbench-instance", help="MO2 instance name to select")
    group.addoption("--devbench-pid", type=int, help="MO2 process ID to select")
    group.addoption(
        "--mo2-results",
        default="test-results/mo2",
        help="Directory for test transcripts and failed captures",
    )
    group.addoption(
        "--visual-update",
        action="store_true",
        help="Replace goldens with new captures instead of comparing",
    )
    parser.addini("devbench_install", "MO2 install directory to select", default="")
    parser.addini("devbench_instance", "MO2 instance name to select", default="")
    parser.addini("devbench_timeout", "HTTP request timeout in seconds", default="30")
    parser.addini(
        "devbench_wait_timeout", "Condition-wait timeout in seconds", default="30"
    )
    parser.addini("devbench_goldens", "Golden image directory", default="tests/goldens")


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "mo2: controls a running MO2 and requires --mo2-tests"
    )
    if config.getoption("mo2_tests") and getattr(config.option, "numprocesses", 0):
        raise pytest.UsageError(
            "MO2 tests share one process. Run without pytest-xdist workers"
        )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("mo2_tests"):
        for item in items:
            if item.get_closest_marker("mo2"):
                item.add_marker(pytest.mark.skip(reason="Enable with --mo2-tests"))


def _client(config):
    timeout = float(config.getini("devbench_timeout"))
    url = config.getoption("devbench_url")
    if url:
        return Client(url, timeout=timeout)
    try:
        instance = find_instance(
            install=config.getoption("devbench_install")
            or config.getini("devbench_install")
            or None,
            instance=config.getoption("devbench_instance")
            or config.getini("devbench_instance")
            or None,
            pid=config.getoption("devbench_pid"),
        )
    except DevBenchError as error:
        pytest.fail(
            f"{error}. Start MO2 with DevBench installed, or select the instance "
            "to test when several are running",
            pytrace=False,
        )
    return Client.for_instance(instance, timeout=timeout)


@contextmanager
def _missing_masters_check_off(client):
    # MO2 runs this check on a worker thread while refreshes rebuild the plugin list
    # on the main thread, so tests that refresh MO2 repeatedly can crash it.
    def setting(action, **value):
        return client.call(
            "settings",
            {
                "action": action,
                "section": "plugins",
                "plugin": "Basic diagnosis plugin",
                "key": "check_missingmasters",
                **value,
            },
        )["value"]

    original = setting("get")
    if original is None:
        yield
        return
    setting("set", value=False)
    try:
        yield
    finally:
        setting("set", value=original)


@pytest.fixture(scope="session")
def devbench_session(request):
    if not request.config.getoption("mo2_tests"):
        pytest.skip("Enable with --mo2-tests")
    with _client(request.config) as client:
        try:
            client.health()
        except (requests.ConnectionError, requests.Timeout) as error:
            pytest.fail(
                f"Cannot connect to DevBench at {client.base_url}. Start MO2 with "
                f"DevBench installed. Connection error: {error}",
                pytrace=False,
            )
        with _missing_masters_check_off(client):
            yield client


@pytest.fixture(name="wait_for", scope="session")
def wait_for_fixture(pytestconfig):
    return partial(
        wait_for, timeout=float(pytestconfig.getini("devbench_wait_timeout"))
    )


@pytest.fixture
def mo2_artifacts(request):
    root = Path(request.config.getoption("mo2_results"))
    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", request.node.nodeid)
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def devbench(devbench_session, mo2_artifacts):
    client = devbench_session
    client.transcript.clear()
    try:
        yield client
    finally:
        (mo2_artifacts / "transcript.json").write_text(
            json.dumps(client.transcript, indent=2), encoding="utf-8"
        )


@pytest.fixture
def visual(request, devbench, mo2_artifacts):
    config = request.config
    return Visual(
        devbench,
        Path(config.rootpath) / config.getini("devbench_goldens"),
        mo2_artifacts,
        update=config.getoption("visual_update"),
    )
