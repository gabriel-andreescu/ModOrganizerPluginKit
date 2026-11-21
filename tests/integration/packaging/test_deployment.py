import json
import os
import shutil
import subprocess
import time

import pytest
from tests.support import deployment_config, locked_file, run


def test_deploys_current_assets(tmp_path, module_project, module_command):
    destinations = [tmp_path / "deploy & one", tmp_path / "deploy two"]
    project = module_project()
    deployment_config(project, {"TestPlugin": [str(p) for p in destinations]})
    nested = project / "payload/nested"
    nested.mkdir()
    run(project, *module_command("deploy"))
    for destination in destinations:
        assert not list(destination.rglob("*"))

    assets = project / "payload"
    (assets / "data").mkdir()
    (assets / "data/fixture.txt").write_text("original")
    run(project, *module_command("deploy"))
    for destination in destinations:
        assert (destination / "data/fixture.txt").read_text() == "original"
        (destination / "retained.txt").write_text("keep")

    # XMake rebuilds inputs newer than its last build, in whole seconds.
    fixture = assets / "data/fixture.txt"
    changed = time.time() + 2
    fixture.write_text("changed")
    os.utime(fixture, (changed, changed))
    run(project, *module_command("deploy"))
    for destination in destinations:
        assert (destination / "data/fixture.txt").read_text() == "changed"
        assert (destination / "retained.txt").read_text() == "keep"


def test_equivalent_destination_paths_preserve_ownership(
    tmp_path, module_project, module_command
):
    destination = tmp_path / "deploy"
    project = module_project()
    deployment_config(project, {"TestPlugin": [str(destination)]})
    data = project / "payload"
    (data / "asset.txt").write_text("original")
    (data / "obsolete.txt").write_text("old")
    run(project, *module_command("deploy"))
    (destination / "unrelated.txt").write_text("keep")

    shutil.rmtree(project / ".xmake")
    equivalent = str(destination) + "/../deploy"
    deployment_config(project, {"TestPlugin": [equivalent, str(destination)]})
    (data / "asset.txt").write_text("updated")
    (data / "obsolete.txt").unlink()
    run(project, *module_command("deploy"))

    assert (destination / "asset.txt").read_text() == "updated"
    assert not (destination / "obsolete.txt").exists()
    assert (destination / "unrelated.txt").read_text() == "keep"


@pytest.mark.parametrize("directory_first", [False, True])
def test_file_directory_replacement(
    tmp_path, module_project, module_command, directory_first
):
    destination = tmp_path / "deploy"
    project = module_project()
    deployment_config(project, {"TestPlugin": [str(destination)]})
    node = project / "payload/node"
    if directory_first:
        node.mkdir()
        (node / "old.txt").write_text("old")
    else:
        node.write_text("old")
    run(project, *module_command("deploy"))
    (destination / "unrelated.txt").write_text("keep")
    if directory_first:
        (node / "old.txt").unlink()
        node.rmdir()
        node.write_text("new")
    else:
        node.unlink()
        node.mkdir()
        (node / "new.txt").write_text("new")
    run(project, *module_command("deploy"))
    expected = "node" if directory_first else "node/new.txt"
    assert (destination / expected).read_text() == "new"
    assert (destination / "unrelated.txt").read_text() == "keep"
    run(project, *module_command("deploy"))
    assert (destination / expected).read_text() == "new"


@pytest.mark.parametrize("conflict", ["file", "parent", "directory"])
def test_unowned_conflict_preserves_all_destinations(
    tmp_path, module_project, module_command, conflict
):
    destinations = [tmp_path / "first", tmp_path / "second"]
    project = module_project()
    deployment_config(project, {"TestPlugin": [str(p) for p in destinations]})
    data = project / "payload"
    (data / "obsolete.txt").write_text("old")
    run(project, *module_command("deploy"))
    (data / "obsolete.txt").unlink()
    (data / "new.txt").write_text("new")
    blocked = destinations[1] / "node"
    if conflict == "parent":
        blocked.write_text("unowned")
        (data / "node").mkdir()
        (data / "node/child.txt").write_text("new")
    elif conflict == "directory":
        blocked.mkdir()
        (blocked / "unowned.txt").write_text("unowned")
        (data / "node").write_text("new")
    else:
        blocked.write_text("unowned")
        (data / "node").write_text("new")
    before = {
        str(file): file.read_bytes()
        for destination in destinations
        for file in destination.rglob("*")
        if file.is_file()
    }
    manifest = project / ".mopk/deployment.lua"
    previous_manifest = manifest.read_bytes()
    result = subprocess.run(
        module_command("deploy"),
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "unowned file" in result.stdout + result.stderr
    assert manifest.read_bytes() == previous_manifest
    assert before == {
        str(file): file.read_bytes()
        for destination in destinations
        for file in destination.rglob("*")
        if file.is_file()
    }


@pytest.mark.parametrize("empty_destinations", [False, True])
def test_removed_destination_leaves_deployed_files(
    tmp_path, module_project, module_command, empty_destinations
):
    project = module_project()
    source = project / "payload/config.ini"
    source.write_text("original")
    deployment_config(project, {"TestPlugin": ["../deploy"]})
    run(project, *module_command("deploy"))
    destination = tmp_path / "deploy/config.ini"
    assert destination.read_text() == "original"
    deployment_config(project, {"TestPlugin": []} if empty_destinations else {})
    source.write_text("not deployed")
    run(project, *module_command("deploy"))
    assert destination.read_text() == "original"


def test_failed_copy_can_be_retried(tmp_path, module_project, module_command):
    destination = tmp_path / "deploy"
    project = module_project()
    deployment_config(project, {"TestPlugin": [str(destination)]})
    data = project / "payload"
    (data / "z-existing.txt").write_text("old")
    run(project, *module_command("deploy"))
    (data / "a-new.txt").write_text("new")
    (data / "z-existing.txt").write_text("updated")
    with locked_file(destination / "z-existing.txt"):
        result = subprocess.run(
            module_command("deploy"),
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert (destination / "a-new.txt").read_text() == "new"
    run(project, *module_command("deploy"))
    assert (destination / "a-new.txt").read_text() == "new"
    assert (destination / "z-existing.txt").read_text() == "updated"


@pytest.mark.parametrize(
    "first,second,nested_destination",
    [
        ("Shared.txt", "shared.txt", False),
        ("node", "node/child.txt", False),
        ("node/child.txt", "node", False),
        ("nested/shared.txt", "shared.txt", True),
    ],
)
def test_target_ownership_conflicts(
    tmp_path, module_project, module_command, first, second, nested_destination
):
    project = module_project("First")
    other = project / "other-payload"
    other.mkdir()
    with (project / "xmake.lua").open("a") as script:
        script.write('\ntarget("Second")\n set_kind("phony")\n')
    source = project / "payload" / first
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("first")
    conflicting = other / second
    conflicting.parent.mkdir(parents=True, exist_ok=True)
    conflicting.write_text("second")
    destination = tmp_path / "deploy"
    second_destination = destination / "nested" if nested_destination else destination
    deployment_config(
        project,
        {
            "First": [str(destination)],
            "Second": [str(second_destination)],
        },
    )
    run(project, *module_command("deploy", "First"))
    result = subprocess.run(
        module_command("deploy", "Second", "other-payload"),
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "Deployment conflict" in output and "First" in output and "Second" in output
    assert (destination / first).read_text() == "first"
    conflicting.unlink()
    (other / "separate.txt").write_text("second")
    run(project, *module_command("deploy", "Second", "other-payload"))
    source.unlink()
    run(project, *module_command("deploy", "First"))
    assert not (destination / first).exists()
    assert (second_destination / "separate.txt").read_text() == "second"


def test_releases_deploy_to_their_own_destinations(
    tmp_path, module_project, module_command
):
    stable, beta = tmp_path / "stable", tmp_path / "beta"
    project = module_project()
    deployment_config(
        project,
        {"TestPlugin": {"2.5.2": [str(stable)], "2.5.3beta12": [str(beta)]}},
    )
    plugin = project / "payload/plugin.dll"
    plugin.write_text("stable")
    run(project, *module_command("deploy", mo2="2.5.2"))
    plugin.write_text("beta")
    run(project, *module_command("deploy", mo2="2.5.3beta12"))
    assert (stable / "plugin.dll").read_text() == "stable"
    assert (beta / "plugin.dll").read_text() == "beta"

    plugin.unlink()
    run(project, *module_command("deploy", mo2="2.5.3beta12"))
    assert not (beta / "plugin.dll").exists()
    assert (stable / "plugin.dll").read_text() == "stable"


def test_destinations_require_release_mapping(tmp_path, module_project, module_command):
    project = module_project()
    settings = project / ".xmake/mopk/deploy.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"TestPlugin": [str(tmp_path / "deploy")]}))
    (project / "payload/plugin.dll").write_text("plugin")
    result = subprocess.run(
        module_command("deploy"),
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "must map MO2 releases" in result.stdout + result.stderr
    assert not (tmp_path / "deploy").exists()
