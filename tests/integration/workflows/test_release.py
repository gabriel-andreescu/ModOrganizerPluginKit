import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.support import ROOT


def run_step(tmp_path, name, environment, *, prefix=""):
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    )
    steps = [step for job in workflow["jobs"].values() for step in job.get("steps", [])]
    script = next(step["run"] for step in steps if step.get("name") == name)
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$ErrorActionPreference = 'Stop'\n" + prefix + script,
        ],
        cwd=tmp_path,
        env={**os.environ, **environment},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "tag,version,valid",
    [
        ("v1.2.3", "1.2.3", True),
        ("v1.2.3", "", True),
        ("1.2.4", "1.2.4", True),
        ("v1.2.4", "1.2.3", False),
        ("main", "1.2.3", False),
    ],
)
def test_release_version(tmp_path, tag, version, valid):
    output = tmp_path / "output"
    result = run_step(
        tmp_path,
        "Validate release version",
        {"RELEASE_TAG": tag, "EXPECTED_VERSION": version, "GITHUB_OUTPUT": str(output)},
    )
    assert (result.returncode == 0) == valid, result.stderr
    if valid:
        assert output.read_text().strip() == f"version={tag.removeprefix('v')}"
    else:
        assert not output.exists()


@pytest.mark.parametrize(
    "date,status,notes,valid",
    [
        ("2026-09-14", "released", "### Fixed\n\n- A fix.\n", True),
        ("2026-02-30", "released", "- A fix.", False),
        ("", "unreleased", "- A fix.", False),
        ("2026-09-14", "yanked", "- A fix.", False),
        ("2026-09-14", "released", " \n", False),
    ],
)
def test_release_notes(tmp_path, date, status, notes, valid):
    source = tmp_path / "notes.md"
    source.write_text(notes)
    result = run_step(
        tmp_path,
        "Prepare release notes",
        {
            "RELEASE_DATE": date,
            "RELEASE_STATUS": status,
            "RELEASE_NOTES": str(source),
            "NOTES_ID": "0000",
            "PACKAGE_NAMES": "",
        },
    )
    assert (result.returncode == 0) == valid, result.stderr
    output = tmp_path / "release-notes/0000.md"
    if valid:
        assert output.read_text() == notes
    else:
        assert not output.exists()


def test_target_changelog_selection(tmp_path):
    directory = tmp_path / "package-metadata"
    directory.mkdir()
    records = [
        ("Main", "2.3.0", None),
        ("Inherited", "1.0.0", None),
        ("Root", "2.3.0", "CHANGELOG.md"),
        ("Translations", "1.1.0", "Tools/Optional/Translations/CHANGELOG.md"),
        ("TranslationsLite", "1.1.0", "Tools/Optional/Translations/CHANGELOG.md"),
        ("OlderTranslations", "1.0.0", "Tools/Optional/Translations/CHANGELOG.md"),
        ("Config", "1.0.0", "Tools/Misc/Config/CHANGELOG.md"),
    ]
    for name, version, changelog in records:
        (directory / f"{name}.json").write_text(
            json.dumps(
                {
                    "target": f"Tools::{name}",
                    "name": name,
                    "version": version,
                    "changelog": changelog,
                }
            )
        )
    output = tmp_path / "output"
    result = run_step(
        tmp_path,
        "Select changelog entries",
        {
            "RELEASE_VERSION": "2.3.0",
            "PROJECT_DIRECTORY": "project",
            "CHANGELOG_PATH": "CHANGELOG.md",
            "PACKAGE_METADATA": "package-metadata",
            "GITHUB_OUTPUT": str(output),
        },
    )
    assert result.returncode == 0, result.stderr
    entries = json.loads(output.read_text().removeprefix("entries="))
    assert len(entries) == 4
    root = entries[0]
    assert (Path(root["path"]).as_posix(), root["version"], root["names"]) == (
        "project/CHANGELOG.md",
        "2.3.0",
        "",
    )
    assert {
        (
            Path(entry["path"]).as_posix(),
            entry["version"],
            frozenset(entry["names"].split(", ")),
        )
        for entry in entries[1:]
    } == {
        ("project/Tools/Misc/Config/CHANGELOG.md", "1.0.0", frozenset({"Config"})),
        (
            "project/Tools/Optional/Translations/CHANGELOG.md",
            "1.0.0",
            frozenset({"OlderTranslations"}),
        ),
        (
            "project/Tools/Optional/Translations/CHANGELOG.md",
            "1.1.0",
            frozenset({"Translations", "TranslationsLite"}),
        ),
    }


def test_combined_release_notes(tmp_path):
    source = tmp_path / "notes.md"
    for identifier, name, version, notes in [
        ("0001", "Translations", "1.1.0", "### Added\n\n- New translations.\n"),
        ("0000", "", "2.3.0", "### Fixed\n\n- A fix.\n"),
    ]:
        source.write_text(notes)
        result = run_step(
            tmp_path,
            "Prepare release notes",
            {
                "RELEASE_DATE": "2026-09-15",
                "RELEASE_STATUS": "released",
                "RELEASE_NOTES": str(source),
                "NOTES_ID": identifier,
                "PACKAGE_NAMES": name,
                "PACKAGE_VERSION": version,
            },
        )
        assert result.returncode == 0, result.stderr
    result = run_step(tmp_path, "Combine release notes", {})
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "release-notes.md").read_text(encoding="utf-8") == (
        "### Fixed\n\n- A fix.\n\n## Translations - v1.1.0\n\n### Added\n\n- New translations.\n"
    )


@pytest.mark.parametrize(
    "packages,attachments",
    [
        (None, []),
        ([], []),
        (
            ["MyPlugin/Main-1.0.0.zip", "MyPlugin/Option-2.0.0.zip"],
            ["Main-1.0.0.zip", "Option-2.0.0.zip"],
        ),
        (
            [
                "Tools/MyPlugin-1.0.0.zip",
                "Extras/MyPlugin-1.0.0.zip",
                "Tools/Optional-2.0.0.zip",
            ],
            [
                "Tools-MyPlugin-1.0.0.zip",
                "Extras-MyPlugin-1.0.0.zip",
                "Optional-2.0.0.zip",
            ],
        ),
        (
            ["Tools/MyPlugin/Alternate.zip", "Extras/MyPlugin/Alternate.zip"],
            ["Tools-MyPlugin-Alternate.zip", "Extras-MyPlugin-Alternate.zip"],
        ),
        (
            ["Tools/MyPlugin/MyPlugin-1.0.0.zip", "Extras/MyPlugin/MyPlugin-1.0.0.zip"],
            ["Tools-MyPlugin-1.0.0.zip", "Extras-MyPlugin-1.0.0.zip"],
        ),
        (
            ["MyPlugin/MyPlugin-1.0.0.zip", "Tools/MyPlugin/MyPlugin-1.0.0.zip"],
            ["MyPlugin-1.0.0.zip", "Tools-MyPlugin-1.0.0.zip"],
        ),
        (
            [
                "my_plugin/my_plugin-1.0.0-MO2-2.5.2.zip",
                "my_plugin/my_plugin-1.0.0-MO2-2.5.3beta12.zip",
            ],
            [
                "my_plugin-1.0.0-MO2-2.5.2.zip",
                "my_plugin-1.0.0-MO2-2.5.3beta12.zip",
            ],
        ),
    ],
)
def test_release_attachments(tmp_path, packages, attachments):
    if packages is not None:
        directory = tmp_path / "packages"
        directory.mkdir()
        for name in packages:
            archive = directory / name
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_bytes(b"zip")
    result = run_step(
        tmp_path,
        "Publish GitHub release",
        {
            "RELEASE_TAG": "v1.0.0",
            "PACKAGE_ARTIFACT": "packages" if packages is not None else "",
        },
        prefix=(
            "function gh {\n"
            "    foreach ($arg in $args) {\n"
            "        if ($arg.EndsWith('.zip') -and [IO.File]::ReadAllText($arg) -ne 'zip') { throw 'Invalid ZIP' }\n"
            "    }\n"
            "    $args | ConvertTo-Json -Compress\n"
            "}\n"
        ),
    )
    if packages == []:
        assert result.returncode != 0
        assert "contains no ZIPs" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert '"--verify-tag"' in result.stdout
        assert '"--notes-file","release-notes.md"' in result.stdout
        arguments = json.loads(result.stdout)
        assert {
            Path(argument).name for argument in arguments if argument.endswith(".zip")
        } == set(attachments)
        for name in packages or []:
            assert (tmp_path / "packages" / name).read_bytes() == b"zip"


def test_release_rejects_colliding_prefixed_names(tmp_path):
    for name in ("Tools/Mod.zip", "Extras/Mod.zip", "Other/Tools-Mod.zip"):
        archive = tmp_path / "packages" / name
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes(b"zip")
    result = run_step(
        tmp_path,
        "Publish GitHub release",
        {"RELEASE_TAG": "v1.0.0", "PACKAGE_ARTIFACT": "packages"},
        prefix="function gh { throw 'Unexpected GitHub call' }\n",
    )
    assert result.returncode != 0
    assert "Duplicate release filename" in result.stderr
    assert "Unexpected GitHub call" not in result.stderr
