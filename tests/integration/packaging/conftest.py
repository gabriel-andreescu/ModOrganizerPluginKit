import json
import subprocess
from pathlib import Path

import pytest

from tests.support import ROOT


@pytest.fixture
def module_project(tmp_path):
    def create(name="TestPlugin"):
        project = tmp_path / "plugin"
        project.mkdir()
        (project / "payload").mkdir()
        (project / "xmake.lua").write_text(
            'option("distdir")\n'
            f'target({json.dumps(name)})\n    set_version("0.1.0")\n    set_kind("phony")\n'
        )
        return project

    return create


@pytest.fixture
def module_command(xmake):
    def command(
        operation, target="TestPlugin", payload="payload", *, config=None, mo2="2.5.2"
    ):
        return [
            xmake,
            "lua",
            str(ROOT / "tests/integration/packaging/run_module.lua"),
            operation,
            target,
            payload,
            json.dumps(config or {"options": {}}),
            mo2,
        ]

    return command


@pytest.fixture
def payload_module(tmp_path, xmake):
    project = tmp_path / "payloads"
    project.mkdir()
    stage = project / "plugins"
    stage.mkdir()
    (project / "xmake.lua").write_text(
        'target("TestPlugin")\n    set_kind("phony")\n    add_installfiles("plugins/(**)")\n'
    )

    def invoke(*, mo2="2.5.2"):
        request = project / "request.json"
        request.write_text(json.dumps({"mo2": mo2}))
        completed = subprocess.run(
            [
                xmake,
                "lua",
                str(ROOT / "tests/integration/packaging/run_payload.lua"),
                str(request),
            ],
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result = json.loads(Path(str(request) + ".result").read_text())
        return project / result["output"]

    return stage, invoke
