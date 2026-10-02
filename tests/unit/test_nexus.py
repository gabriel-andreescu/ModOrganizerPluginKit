import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from tests.support import ROOT

MOD_ID = "7318624464804"


def step(name):
    workflow = yaml.safe_load((ROOT / ".github/workflows/nexus.yml").read_text())
    return next(
        step["run"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if step.get("name") == name
    )


def run_step(name):
    namespace = {"__name__": "test"}
    exec(step(name), namespace)  # noqa: S102
    return namespace


def responses(*bodies):
    return [io.BytesIO(json.dumps(body).encode()) for body in bodies]


def test_package_destinations_and_shared_changelogs():
    namespace = run_step("Plan Nexus publication")
    stable = {
        "target": "MyPlugin",
        "name": "MyPlugin",
        "version": "1.1.0",
        "archive": "MyPlugin/MyPlugin-1.1.0-MO2-2.5.2.zip",
        "nexus": {
            "game": "skyrimspecialedition",
            "mod_id": MOD_ID,
            "file_id": "1",
            "category": "main",
            "primary": True,
            "display_name": "MyPlugin for MO2 2.5.2",
        },
    }
    beta = {
        **stable,
        "archive": "MyPlugin/MyPlugin-1.1.0-MO2-2.5.3beta12.zip",
        "nexus": {
            **stable["nexus"],
            "file_id": "2",
            "primary": False,
            "display_name": "MyPlugin for MO2 2.5.3beta12",
        },
    }
    extras = {
        **stable,
        "target": "Extras",
        "name": "Extras",
        "version": "2.0.0",
        "changelog": "extras/CHANGELOG.md",
        "archive": "Extras/Extras-2.0.0-MO2-2.5.2.zip",
        "nexus": {
            "game": "skyrimspecialedition",
            "mod_id": MOD_ID,
            "file_id": "3",
            "category": "optional",
        },
    }
    notes = {
        "0000": {
            "version": "1.1.0",
            "path": "CHANGELOG.md",
            "html": "<h3>Fixed</h3>\n<ul><li>Settings <code>reload</code> &amp; saving.</li></ul>",
        },
        "0001": {
            "version": "2.0.0",
            "path": "extras/CHANGELOG.md",
            "html": '<h3>Added</h3><ul><li>Extras for <a href="https://example.com">MyPlugin</a>.</li></ul>',
        },
    }
    files, changelogs = namespace["plan"](
        [stable, beta, extras, {**stable, "target": "Local", "nexus": None}],
        notes,
        ".",
    )
    assert {
        (file["file_id"], file["category"], file["primary"], file["name"])
        for file in files
    } == {
        ("1", "main", True, "MyPlugin for MO2 2.5.2"),
        ("2", "main", False, "MyPlugin for MO2 2.5.3beta12"),
        ("3", "optional", False, "Extras"),
    }
    assert {file["domain"] for file in files} == {"skyrimspecialedition"}
    assert {entry["version"]: entry["entries"] for entry in changelogs} == {
        "1.1.0": ["Fixed: Settings reload & saving."],
        "2.0.0": ["Added: Extras for MyPlugin (https://example.com)."],
    }
    assert {entry["page_id"] for entry in changelogs} == {"192420"}


@pytest.mark.parametrize("game", [None, "Skyrim Special Edition", "../games"])
def test_plan_rejects_invalid_game_domains(game):
    namespace = run_step("Plan Nexus publication")
    package = {
        "target": "MyPlugin",
        "name": "MyPlugin",
        "version": "1.0.0",
        "archive": "MyPlugin/MyPlugin-1.0.0-MO2-2.5.2.zip",
        "nexus": {"game": game, "mod_id": MOD_ID, "file_id": "1", "category": "main"},
    }
    notes = {"0000": {"version": "1.0.0", "path": "CHANGELOG.md", "html": ""}}
    with pytest.raises(ValueError, match="game domain"):
        namespace["plan"]([package], notes, ".")


@pytest.fixture
def uploaded_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    archive = Path("packages/MyPlugin/plugin.zip")
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"fixture")
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("NEXUSMODS_API_KEY", "fixture")
    monkeypatch.setenv(
        "NEXUS_FILE",
        json.dumps(
            {
                "file_id": "17",
                "mod_id": MOD_ID,
                "domain": "skyrimspecialedition",
                "version": "1.1.0",
                "archive": "MyPlugin/plugin.zip",
                "name": "MyPlugin",
            }
        ),
    )
    return output


def test_retry_skips_uploaded_file(uploaded_file):
    with patch(
        "urllib.request.urlopen",
        side_effect=responses(
            {"id": 1704},
            {"data": {"mod_files": [{"id": "17"}]}},
            {"data": {"versions": [{"version": "1.0.0"}, {"version": "1.1.0"}]}},
        ),
    ) as request:
        run_step("Check Nexus file")
    assert [call.args[0].full_url for call in request.call_args_list] == [
        "https://api.nexusmods.com/v1/games/skyrimspecialedition.json",
        f"https://api.nexusmods.com/v3/mods/{MOD_ID}/files",
        "https://api.nexusmods.com/v3/mod-files/17/versions",
    ]
    assert uploaded_file.read_text().strip() == "exists=true"


def test_mod_from_another_game_is_rejected(uploaded_file):
    with (
        patch("urllib.request.urlopen", side_effect=responses({"id": 1151})) as request,
        pytest.raises(ValueError, match="does not belong to skyrimspecialedition"),
    ):
        run_step("Check Nexus file")
    assert request.call_count == 1
    assert not uploaded_file.exists()


def test_changelog_retry_only_posts_missing_entries(monkeypatch):
    monkeypatch.setenv("NEXUSMODS_API_KEY", "fixture")
    monkeypatch.setenv(
        "NEXUS_CHANGELOG",
        json.dumps(
            {
                "mod_id": MOD_ID,
                "page_id": "192420",
                "domain": "skyrimspecialedition",
                "version": "1.1.0",
                "entries": ["Fixed: Saving & loading.", "Added: New menu."],
            }
        ),
    )
    existing = {"1.1.0": ["Fixed: Saving &amp; loading."]}
    with patch(
        "urllib.request.urlopen",
        side_effect=[io.BytesIO(json.dumps(existing).encode()), io.BytesIO(b"{}")],
    ) as request:
        run_step("Publish Nexus changelog")
    assert json.loads(request.call_args.args[0].data) == {
        "version": "1.1.0",
        "changelog": "Added: New menu.",
    }
    existing["1.1.0"].append("Added: New menu.")
    with patch(
        "urllib.request.urlopen", return_value=io.BytesIO(json.dumps(existing).encode())
    ) as request:
        run_step("Publish Nexus changelog")
    assert request.call_count == 1
