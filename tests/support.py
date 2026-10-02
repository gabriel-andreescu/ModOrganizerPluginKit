import ctypes
import json
import subprocess
import zipfile
from contextlib import contextmanager
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VERSION = yaml.safe_load((ROOT / "copier.yml").read_text(encoding="utf-8"))[
    "mopk_version"
]["default"]


@contextmanager
def locked_file(path):
    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.restype = ctypes.c_void_p
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    close_handle = ctypes.windll.kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    handle = create_file(str(path), 0x80000000, 0, None, 3, 0x80, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        yield
    finally:
        close_handle(handle)


def deployment_config(project, targets, release="2.5.2"):
    settings = project / ".xmake/mopk/deploy.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    releases = {
        target: destinations
        if isinstance(destinations, dict)
        else {release: destinations}
        for target, destinations in targets.items()
    }
    settings.write_text(json.dumps(releases), encoding="utf-8")


def run(directory, *command):
    result = subprocess.run(
        command,
        cwd=directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def archive_files(archive):
    with zipfile.ZipFile(archive) as zipped:
        return {
            name.replace("\\", "/"): zipped.read(name)
            for name in zipped.namelist()
            if not name.endswith("/")
        }
