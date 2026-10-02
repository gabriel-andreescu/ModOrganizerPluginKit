import hashlib
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir

import pytest
from filelock import FileLock

from tests.support import ROOT, VERSION, run


@pytest.fixture(scope="session")
def xmake(worker_id):
    executable = shutil.which("xmake")
    assert executable, "Install XMake to run build integration tests."
    # Dependency builds and resource copies can exceed Windows path limits
    # beneath deeply nested pytest directories.
    checkout = hashlib.sha256(str(ROOT).encode()).hexdigest()[:8]
    cache = Path(
        os.environ.get("MOPK_TEST_CACHE", Path(gettempdir()) / "mopk-tests" / checkout)
    )
    state = cache / worker_id
    state.mkdir(parents=True, exist_ok=True)
    with (
        FileLock(state / "session.lock"),
        TemporaryDirectory(prefix="mopk-xmake-") as state_dir,
        pytest.MonkeyPatch.context() as environment,
    ):
        environment.setenv("XMAKE_GLOBALDIR", str(state / "global"))
        environment.setenv("XMAKE_PKG_CACHEDIR", str(state / "downloads"))
        environment.setenv("XMAKE_TMPDIR", state_dir)
        environment.setenv("XMAKE_PKG_INSTALLDIR", str(state / "packages"))
        yield executable


@pytest.fixture(scope="session")
def mopk_addon(tmp_path_factory, xmake):
    xrepo = shutil.which("xrepo")
    assert xrepo, "Install XMake to run build integration tests."
    directory = tmp_path_factory.mktemp("addon")
    run(directory, xmake, "repo", "--add", "--global", "mopk", ROOT.as_posix())
    run(
        directory,
        xrepo,
        "install",
        "--addon",
        "-y",
        f"--debugdir={ROOT}",
        f"mopk {VERSION}",
    )
    return xmake
