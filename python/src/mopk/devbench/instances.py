"""Discovery of live MO2 DevBench instances from their instance records."""

from __future__ import annotations

import ctypes
import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from .errors import DevBenchError


@dataclass(frozen=True)
class Instance:
    base_url: str
    pid: int
    session: str
    install: str
    instance: str


def _path_key(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def _valid(record, file: Path) -> bool:
    pid = record.get("pid")
    port = record.get("port")
    executable = record.get("exe")
    return (
        type(pid) is int
        and pid > 0
        and file.name == f"{pid}.json"
        and type(port) is int
        and 1 <= port <= 65535
        and isinstance(record.get("session"), str)
        and record["session"] != ""
        and isinstance(executable, str)
        and os.path.isabs(executable)
        and os.path.basename(executable).lower() == "modorganizer.exe"
        and isinstance(record.get("install"), str)
        and isinstance(record.get("instance"), str)
    )


def _selected(record, install: str | None, instance: str | None, pid: int | None):
    return (
        (pid is None or record["pid"] == pid)
        and (install is None or _path_key(record["install"]) == _path_key(install))
        and (instance is None or record["instance"].lower() == instance.lower())
    )


def _running(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.GetExitCodeProcess.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    process_query_limited_information = 0x1000
    still_active = 259
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_uint32()
        return bool(
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            and code.value == still_active
        )
    finally:
        kernel32.CloseHandle(handle)


def _live(record, session: requests.Session, timeout: float) -> bool:
    try:
        response = session.get(
            f"http://127.0.0.1:{record['port']}/api/health", timeout=timeout
        )
        if not response.ok:
            return False
        health = response.json()
    except (requests.RequestException, ValueError):
        return False
    return (
        isinstance(health, dict)
        and health.get("session") == record["session"]
        and health.get("pid") == record["pid"]
        and health.get("port") == record["port"]
        and isinstance(health.get("exe"), str)
        and _path_key(health["exe"]) == _path_key(record["exe"])
    )


def _label(install: str | None, instance: str | None, pid: int | None) -> str:
    selection = [
        value
        for value in (
            install,
            None if instance is None else f"instance {instance}",
            None if pid is None else f"PID {pid}",
        )
        if value is not None
    ]
    return f"MO2 ({', '.join(selection)})" if selection else "MO2"


def records_directory(local_app_data: str | Path | None = None) -> Path:
    root = local_app_data or os.environ.get("LOCALAPPDATA")
    if not root:
        raise DevBenchError(
            "LOCALAPPDATA is unavailable, so DevBench instances cannot be discovered"
        )
    return Path(root) / "devbench" / "mo2" / "instances"


def find_instance(
    *,
    install: str | Path | None = None,
    instance: str | None = None,
    pid: int | None = None,
    local_app_data: str | Path | None = None,
    timeout: float = 3,
) -> Instance:
    """Return the one live MO2 matching every given selector."""
    install = None if install is None else os.path.abspath(install)
    label = _label(install, instance, pid)
    directory = records_directory(local_app_data)
    matches: dict[str, Instance] = {}
    with requests.Session() as session:
        session.trust_env = False
        for file in sorted(directory.glob("*.json")) if directory.is_dir() else []:
            try:
                record = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(record, dict) or not _valid(record, file):
                continue
            if not _selected(record, install, instance, pid):
                continue
            # A killed MO2 leaves its record behind. Probing those ports queues requests on whichever
            # MO2 holds them now, and enough of them make a live instance miss the timeout.
            if not _running(record["pid"]):
                continue
            if _live(record, session, timeout):
                matches[record["session"]] = Instance(
                    base_url=f"http://127.0.0.1:{record['port']}",
                    pid=record["pid"],
                    session=record["session"],
                    install=record["install"],
                    instance=record["instance"],
                )
    if not matches:
        raise DevBenchError(f"MO2 not running: {label}")
    if len(matches) != 1:
        found = ", ".join(
            f"PID {match.pid} ({match.instance or match.install})"
            for match in matches.values()
        )
        raise DevBenchError(
            f"Multiple live MO2 instances found: {found}. "
            "Select one with install, instance or pid"
        )
    return next(iter(matches.values()))
