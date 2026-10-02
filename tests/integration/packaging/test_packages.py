import json
import subprocess

import pytest
from tests.support import archive_files, locked_file, run


def planned_files(path):
    return json.loads(path.read_text())


def records(project):
    return [
        json.loads(path.read_text())
        for path in (project / ".xmake/mopk/packages").glob("*.json")
    ]


def test_empty_payload_produces_no_package(module_project, module_command):
    project = module_project()
    nested = project / "payload/nested"
    nested.mkdir()
    (nested / ".gitkeep").touch()
    run(project, *module_command("package"))
    assert not list(project.glob("build/dist/**/*.zip"))


def test_package_contents_omit_placeholders(module_project, module_command):
    project = module_project()
    data = project / "payload/data"
    data.mkdir()
    (data / "fixture.txt").write_text("original")
    nested = project / "payload/nested"
    nested.mkdir()
    (nested / ".gitkeep").touch()
    nexus = {
        "game": "skyrimspecialedition",
        "mod_id": "7318624464804",
        "files": {"2.5.2": {"file_id": "7995705", "category": "main"}},
    }
    run(
        project,
        *module_command(
            "package",
            config={"options": {"changelog": "extras/CHANGELOG.md", "nexus": nexus}},
        ),
    )
    output = project / "build/dist/TestPlugin"
    expected = {
        "TestPlugin-0.1.0-MO2-2.5.2.zip": {"data/fixture.txt": "original"},
    }
    assert {file.name for file in output.iterdir()} == expected.keys()
    for name, contents in expected.items():
        assert planned_files(output / name) == contents
    assert records(project) == [
        {
            "target": "TestPlugin",
            "name": "TestPlugin",
            "version": "0.1.0",
            "archive": "TestPlugin/TestPlugin-0.1.0-MO2-2.5.2.zip",
            "changelog": "extras/CHANGELOG.md",
            "nexus": {
                "game": "skyrimspecialedition",
                "mod_id": "7318624464804",
                "file_id": "7995705",
                "category": "main",
                "display_name": "TestPlugin for MO2 2.5.2",
            },
        }
    ]


def test_releases_keep_separate_packages(module_project, module_command):
    project = module_project()
    (project / "payload/plugin.dll").write_text("plugin")
    nexus = {
        "game": "skyrimspecialedition",
        "mod_id": "7318624464804",
        "files": {"2.5.2": {"file_id": "1", "category": "main", "primary": True}},
    }
    config = {"options": {"nexus": nexus}}
    for release in ("2.5.2", "2.5.3beta12"):
        run(project, *module_command("package", config=config, mo2=release))
    output = project / "build/dist/TestPlugin"
    assert {file.name for file in output.iterdir()} == {
        "TestPlugin-0.1.0-MO2-2.5.2.zip",
        "TestPlugin-0.1.0-MO2-2.5.3beta12.zip",
    }
    assert {
        record["archive"]: record.get("nexus", {}).get("file_id")
        for record in records(project)
    } == {
        "TestPlugin/TestPlugin-0.1.0-MO2-2.5.2.zip": "1",
        "TestPlugin/TestPlugin-0.1.0-MO2-2.5.3beta12.zip": None,
    }

    script = project / "xmake.lua"
    script.write_text(script.read_text().replace('"0.1.0"', '"0.2.0"'))
    run(project, *module_command("package", config=config, mo2="2.5.2"))
    assert {file.name for file in output.iterdir()} == {
        "TestPlugin-0.2.0-MO2-2.5.2.zip",
        "TestPlugin-0.1.0-MO2-2.5.3beta12.zip",
    }


def test_distribution_directory_has_separate_ownership(
    module_project, module_command, xmake
):
    project = module_project()
    (project / "payload/asset.txt").write_text("asset")
    run(project, *module_command("package"))
    destination = project / "custom/TestPlugin/TestPlugin-0.1.0-MO2-2.5.2.zip"
    destination.parent.mkdir(parents=True)
    destination.write_text("unowned")
    run(project, xmake, "f", "-y", "--distdir=custom")
    result = subprocess.run(
        module_command("package"),
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0 and "unowned file" in result.stdout + result.stderr
    assert destination.read_text() == "unowned"
    assert (project / "build/dist/TestPlugin/TestPlugin-0.1.0-MO2-2.5.2.zip").is_file()


@pytest.mark.parametrize("change", ["empty", "renamed", "version"])
def test_obsolete_packages_are_removed(module_project, module_command, change):
    project = module_project()
    asset = project / "payload/asset.txt"
    asset.write_text("main")
    run(project, *module_command("package"))
    output = project / "build/dist/TestPlugin"
    main_zip = output / "TestPlugin-0.1.0-MO2-2.5.2.zip"
    assert planned_files(main_zip) == {"asset.txt": "main"}
    (output / "unrelated.zip").write_bytes(b"keep")
    (project / "build/dist/unrelated.txt").write_text("keep")

    if change == "empty":
        asset.unlink()
        asset.with_name(".gitkeep").touch()
    elif change == "version":
        script = project / "xmake.lua"
        script.write_text(script.read_text().replace('"0.1.0"', '"0.2.0"'))
    options = {"package_name": "Renamed"} if change == "renamed" else {}
    run(project, *module_command("package", config={"options": options}))

    expected = {"unrelated.zip"}
    if change == "renamed":
        expected.add("Renamed-0.1.0-MO2-2.5.2.zip")
    elif change == "version":
        expected.add("TestPlugin-0.2.0-MO2-2.5.2.zip")
    assert {p.name for p in output.iterdir()} == expected
    assert (output / "unrelated.zip").read_bytes() == b"keep"
    assert (project / "build/dist/unrelated.txt").read_text() == "keep"
    if change == "empty":
        assert not records(project)
    else:
        record = records(project)[0]
        assert (
            record["archive"]
            == f"TestPlugin/{next(iter(expected - {'unrelated.zip'}))}"
        )
        assert "changelog" not in record


@pytest.mark.parametrize("namespaced", [False, True])
def test_targets_can_share_package_names(module_project, module_command, namespaced):
    first = "Tools::MyPlugin" if namespaced else "MyPluginTools"
    second = "Extras::MyPlugin" if namespaced else "MyPluginExtras"
    project = module_project(first)
    options = {} if namespaced else {"package_name": "MyPlugin"}
    script = project / "xmake.lua"
    script.write_text(
        script.read_text()
        + f'\ntarget("{second}")\n    set_kind("phony")\n    set_version("0.1.0")\n'
    )
    for folder in ("Tools", "Extras"):
        data = project / folder / "plugins"
        data.mkdir(parents=True, exist_ok=True)
        (data / "asset.txt").write_text(folder)
    for target, folder in [(first, "Tools"), (second, "Extras")]:
        run(
            project,
            *module_command(
                "package", target, f"{folder}/plugins", config={"options": options}
            ),
        )
    first_output = project / "build/dist" / first.replace("::", "/")
    second_output = project / "build/dist" / second.replace("::", "/")
    name = "MyPlugin-0.1.0-MO2-2.5.2.zip"
    assert planned_files(first_output / name) == {"asset.txt": "Tools"}
    assert planned_files(second_output / name) == {"asset.txt": "Extras"}
    before = {p.name: p.read_bytes() for p in second_output.iterdir()}
    (project / "Tools/plugins/asset.txt").unlink()
    run(
        project,
        *module_command("package", first, "Tools/plugins", config={"options": options}),
    )
    assert not list(first_output.iterdir())
    assert {p.name: p.read_bytes() for p in second_output.iterdir()} == before


def test_targets_package_independent_versions(module_project, module_command):
    project = module_project("Tools::MyPlugin")
    packages = [
        ("Tools::MyPlugin", "0.1.0", "payload"),
        ("Tools::MyPlugin::Extras", "1.0.0", "extras"),
        ("Tools::MyPlugin::AlternateConfig", "1.1.0", "config"),
    ]
    with (project / "xmake.lua").open("a") as script:
        for target, version, _ in packages[1:]:
            script.write(
                f'\ntarget("{target}")\n    set_kind("phony")\n'
                f'    set_version("{version}")\n'
            )
    for target, _, directory in packages:
        payload = project / directory
        payload.mkdir(parents=True, exist_ok=True)
        (payload / "asset.txt").write_text(target)
        run(project, *module_command("package", target, directory))
    for target, version, _ in packages:
        name = target.split("::")[-1]
        output = project / "build/dist" / target.replace("::", "/")
        assert planned_files(output / f"{name}-{version}-MO2-2.5.2.zip") == {
            "asset.txt": target
        }


@pytest.mark.parametrize("conflict", ["unowned", "directory"])
def test_package_conflicts_preserve_output(module_project, module_command, conflict):
    project = module_project()
    (project / "payload/asset.txt").write_text("main")
    run(project, *module_command("package"))
    output = project / "build/dist/TestPlugin"
    old_zip = output / "TestPlugin-0.1.0-MO2-2.5.2.zip"
    previous = old_zip.read_bytes()
    script = project / "xmake.lua"
    script.write_text(script.read_text().replace('"0.1.0"', '"0.2.0"'))
    conflict_path = output / "TestPlugin-0.2.0-MO2-2.5.2.zip"
    if conflict == "directory":
        conflict_path.mkdir()
        (conflict_path / "unrelated.txt").write_text("keep")
    else:
        conflict_path.write_bytes(b"keep")
    result = subprocess.run(
        module_command("package"),
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert old_zip.read_bytes() == previous
    if conflict == "unowned":
        assert conflict_path.read_bytes() == b"keep"
    elif conflict == "directory":
        assert (conflict_path / "unrelated.txt").read_text() == "keep"


@pytest.mark.parametrize("locked", ["source", "output"])
def test_failed_packaging_can_be_retried(module_project, module_command, locked):
    project = module_project()
    source = project / "payload/asset.txt"
    source.write_text("original")
    run(project, *module_command("package-real"))
    output = project / "build/dist/TestPlugin"
    old_zip = output / "TestPlugin-0.1.0-MO2-2.5.2.zip"
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    script = project / "xmake.lua"
    script.write_text(script.read_text().replace('"0.1.0"', '"0.2.0"'))
    source.write_text("updated")
    with locked_file(source if locked == "source" else old_zip):
        result = subprocess.run(
            module_command("package-real"),
            cwd=project,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        if locked == "source":
            assert {p.name: p.read_bytes() for p in output.iterdir()} == before
    assert old_zip.read_bytes() == before[old_zip.name]
    run(project, *module_command("package-real"))
    assert not old_zip.exists()
    assert archive_files(output / "TestPlugin-0.2.0-MO2-2.5.2.zip") == {
        "asset.txt": b"updated"
    }
