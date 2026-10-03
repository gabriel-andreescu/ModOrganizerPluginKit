import hashlib
import os
from pathlib import Path

import pefile
import pytest
from copier import run_copy
from tests.support import ROOT, archive_files, deployment_config, run

pytestmark = pytest.mark.skipif(
    os.environ.get("MOPK_TEST_NATIVE_PLUGINS") != "1",
    reason="Set MOPK_TEST_NATIVE_PLUGINS=1 to build the native plugin consumer.",
)

RELEASES = ["2.5.2", "2.5.3beta12"]


@pytest.fixture(scope="session")
def compiler_identity(mopk_addon):
    identity = run(
        ROOT,
        mopk_addon,
        "lua",
        "-c",
        'import("core.tool.toolchain"); import("core.base.json"); '
        'local tc = toolchain.load("msvc", {plat = "windows", arch = "x64"}); '
        "assert(tc:check()); "
        'print(json.encode({tc:config("vs_toolset"), tc:config("vs_sdkver")}))',
    ).stdout.splitlines()[-1]
    identity += run(ROOT, mopk_addon, "--version").stdout.splitlines()[0]
    return identity


@pytest.fixture
def native_xmake(monkeypatch, mopk_addon, compiler_identity):
    # XMake's package hash omits recipe contents and compiler versions.
    digest = hashlib.sha256(compiler_identity.encode())
    for name in ("mo2-uibase", "devbench-api"):
        for source in sorted((ROOT / "packages" / name[0] / name).rglob("*")):
            if source.is_file():
                digest.update(source.relative_to(ROOT).as_posix().encode() + b"\0")
                digest.update(source.read_bytes())
    cache = Path(os.environ["XMAKE_PKG_INSTALLDIR"]) / digest.hexdigest()[:16]
    monkeypatch.setenv("XMAKE_PKG_INSTALLDIR", str(cache))
    return mopk_addon


def generate(project):
    run_copy(
        str(ROOT),
        project,
        vcs_ref="HEAD",
        data={
            "project_name": "sample_plugin",
            "author": "Test Author",
            "description": "Plugin package test",
            "devbench_api": True,
            "mopk_repository": ROOT.as_posix(),
        },
        defaults=True,
        quiet=True,
    )


@pytest.mark.parametrize("mo2", RELEASES)
def test_plugin_package(tmp_path, native_xmake, mo2):
    project = tmp_path / "plugin"
    generate(project)
    run(
        project,
        native_xmake,
        "f",
        "-y",
        "-a",
        "x64",
        "--toolchain=msvc",
        f"--mo2={mo2}",
    )
    destination = project / "deployed"
    deployment_config(project, {"sample_plugin": [str(destination)]}, release=mo2)
    run(project, native_xmake, "package", "-y")

    archive = project / f"build/dist/sample_plugin/sample_plugin-0.1.0-MO2-{mo2}.zip"
    files = archive_files(archive)
    assert set(files) == {"sample_plugin.dll", "sample_plugin.pdb"}
    built = project / f"build/mo2-{mo2}/windows/x64/releasedbg/sample_plugin.dll"
    assert files["sample_plugin.dll"] == built.read_bytes()
    assert files["sample_plugin.pdb"] == built.with_suffix(".pdb").read_bytes()
    for name, contents in files.items():
        assert (destination / name).read_bytes() == contents

    dll = files["sample_plugin.dll"]
    with pefile.PE(data=dll) as pe:
        exports = {symbol.name for symbol in pe.DIRECTORY_ENTRY_EXPORT.symbols}
        assert b"qt_plugin_instance" in exports
        assert pe.FILE_HEADER.Machine == 0x8664
    metadata = dll.find(b"QTMETADATA !")
    assert metadata >= 0
    # The header continues with the metadata version, the Qt major and minor
    # versions, then architecture flags with 0x80 for debug builds.
    assert dll[metadata + 13 : metadata + 15] == bytes([6, 7])
    assert not dll[metadata + 15] & 0x80
    assert b"sample_plugin" in dll[metadata : metadata + 256]
    assert "Test Author".encode("utf-16-le") in dll

    objects = list((project / f"build/mo2-{mo2}/.objs").rglob("DevBenchAPI.cpp.obj"))
    assert len(objects) == 1
    modified = objects[0].stat().st_mtime_ns
    run(project, native_xmake, "build", "-y")
    assert objects[0].stat().st_mtime_ns == modified
