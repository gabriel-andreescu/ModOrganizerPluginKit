import json

import pytest
import yaml
from copier import run_copy

from tests.support import ROOT, VERSION, archive_files, deployment_config, run


def generate(destination, **answers):
    run_copy(
        str(ROOT),
        destination,
        vcs_ref="HEAD",
        data={"mopk_repository": ROOT.as_posix(), **answers},
        defaults=True,
        quiet=True,
    )


@pytest.mark.parametrize("pre_commit", [True, False])
def test_plugin_layout(tmp_path, pre_commit):
    generate(tmp_path, project_name="my-plugin", pre_commit=pre_commit)
    script = (tmp_path / "xmake.lua").read_text()
    assert 'set_basename("my-plugin")' in script
    assert "@addon/mopk/plugin" in script
    assert 'add_packages("qt6base", "mo2-uibase")' in script
    assert (
        'Q_PLUGIN_METADATA(IID "my-plugin")' in (tmp_path / "src/Plugin.h").read_text()
    )
    assert (tmp_path / "src/PCH.h").is_file()
    assert (tmp_path / ".clangd").is_file()
    assert (tmp_path / ".pre-commit-config.yaml").is_file() == pre_commit
    assert not (tmp_path / ".xmake").exists()


@pytest.mark.parametrize("devbench_tests", [True, False])
def test_devbench_tests(tmp_path, devbench_tests):
    generate(tmp_path, project_name="MyPlugin", devbench_tests=devbench_tests)
    assert (tmp_path / "tests/mo2/test_startup.py").is_file() == devbench_tests
    hooks = (tmp_path / ".pre-commit-config.yaml").read_text()
    assert ("ruff-check" in hooks) == devbench_tests
    for name in ("settings.json", "extensions.json"):
        json.loads((tmp_path / ".vscode" / name).read_text())
    if devbench_tests:
        project = (tmp_path / "pyproject.toml").read_text()
        assert 'name = "myplugin-tests"' in project
        assert "modorganizer-plugin-kit[test]" in project
        assert (
            tmp_path / "tests/conftest.py"
        ).read_text() == 'pytest_plugins = ["mopk.devbench.pytest_plugin"]\n'
    else:
        assert not (tmp_path / "pyproject.toml").exists()


def test_deployment_answers(tmp_path):
    stable = tmp_path / "stable"
    generate(
        tmp_path / "project",
        project_name="my_plugin",
        deploy_2_5_2=f" {stable} ; {tmp_path / 'other'} ",
    )
    settings = json.loads(
        (tmp_path / "project/.xmake/mopk/deploy.json").read_text(encoding="utf-8")
    )
    assert settings == {"my_plugin": {"2.5.2": [str(stable), str(tmp_path / "other")]}}
    answers = yaml.safe_load((tmp_path / "project/.copier-answers.yml").read_text())
    assert "deploy_2_5_2" not in answers
    assert "deploy_2_5_3beta12" not in answers


def test_package_composition(tmp_path, mopk_addon):
    project = tmp_path / "project"
    generate(project)
    (project / "base.txt").write_text("base")
    (project / "private.txt").write_text("private")
    (project / "output.txt").write_text("compiled")
    (project / "override.txt").write_text("override")
    (project / "xmake.lua").write_text(
        f"add_repositories({json.dumps('mopk ' + ROOT.as_posix())})\n"
        f'add_addons("mopk {VERSION}")\nincludes("@addon/mopk/project")\n'
        'target("Private")\n set_kind("phony")\n set_default(false)\n add_installfiles("private.txt")\n'
        'target("Compiler")\n set_kind("phony")\n set_default(false)\n'
        ' add_deps("Private")\n add_installfiles("output.txt")\n'
        'target("Tools::MyPlugin")\n set_version("1.0.0")\n'
        ' add_rules("@addon/mopk/package", {targets = {"Compiler"}})\n'
        ' add_installfiles("base.txt")\n'
        'target("Extras::MyPlugin")\n set_version("2.0.0")\n'
        ' add_rules("@addon/mopk/package", {targets = {"Compiler"}})\n'
        ' add_installfiles("override.txt", {filename = "output.txt"})\n'
    )
    deployment_config(
        project,
        {
            "Tools::MyPlugin": {
                "2.5.2": [str(tmp_path / "stable")],
                "2.5.3beta12": [str(tmp_path / "beta")],
            }
        },
    )
    run(project, mopk_addon, "package", "-y")
    assert archive_files(
        project / "build/dist/Tools/MyPlugin/MyPlugin-1.0.0-MO2-2.5.2.zip"
    ) == {"base.txt": b"base", "output.txt": b"compiled"}
    assert archive_files(
        project / "build/dist/Extras/MyPlugin/MyPlugin-2.0.0-MO2-2.5.2.zip"
    ) == {"output.txt": b"override"}
    assert (tmp_path / "stable/output.txt").read_text() == "compiled"
    assert not (tmp_path / "stable/private.txt").exists()
    assert not (tmp_path / "beta").exists()


def test_tooling_only_keeps_existing_project(tmp_path):
    existing = {
        "README.md": "# Existing project\n",
        "xmake.lua": 'set_project("Existing")\n',
        "src/Plugin.cpp": "existing source\n",
    }
    for name, contents in existing.items():
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)
    generate(tmp_path, tooling_only=True)
    for name, contents in existing.items():
        assert (tmp_path / name).read_text() == contents
    generated = {
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    } - existing.keys()
    assert generated == {
        ".clang-format",
        ".clang-tidy",
        ".clangd",
        ".copier-answers.yml",
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".prettierignore",
        ".prettierrc.json",
        ".stylua.toml",
        ".vscode/extensions.json",
        ".vscode/settings.json",
    }
