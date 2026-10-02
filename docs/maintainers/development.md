# MOPK development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). From the MOPK root:

```powershell
uv sync --locked
uv run pre-commit install
```

## Formatting and lint

The [commit hooks](../../.pre-commit-config.yaml) format staged files with
Prettier, Ruff and StyLua, and apply Ruff lint fixes. Prettier uses
[`proseWrap: "always"`](https://prettier.io/docs/options#prose-wrap). StyLua
uses four-space indentation. Run the hooks on all tracked files with:

```powershell
uv run pre-commit run --all-files
```

CI runs the same checks. Jinja templates and the vendored beta SDK are excluded
from formatting.

## XMake

Requires [XMake 3.1.1](https://github.com/xmake-io/xmake/releases/tag/v3.1.1).

## Tests

Run the unit tests:

```powershell
uv run pytest
```

These cover Nexus publication planning and its API calls, and the DevBench
client, instance discovery and golden checks.

Integration tests require Windows, Git, PowerShell 7 and XMake:

```powershell
uv run pytest tests/integration -n 4
```

These cover generated projects, deployment, packaging, release scripts and the
pytest plugin lifecycle. Use `-n 0` for serial execution. Generator tests copy
the checkout's `HEAD` commit, including uncommitted changes.

Set `MOPK_TEST_CACHE` to choose the XMake test cache directory.

## Native tests

Requires Visual Studio 2022 with the C++ toolset and Windows SDK.

To build and inspect plugin packages for every supported MO2 release:

```powershell
$env:MOPK_TEST_NATIVE_PLUGINS = "1"
uv run pytest tests/native/test_plugins.py
Remove-Item Env:MOPK_TEST_NATIVE_PLUGINS
```

The consumer tests build a generated plugin against the uibase and DevBench
revisions pinned in `packages/`. They check package installation, the DLL's Qt
metadata and exports, deployed files and ZIP contents.

## Plugins

Generate a plugin from the local checkout, then build, package and load it for
every supported MO2 release as described in
[validating changes](../../CONTRIBUTING.md#validate-rule-and-package-changes):

```powershell
uv run copier copy --defaults --trust --vcs-ref HEAD -d project_name=sample_plugin C:/path/to/ModOrganizerPluginKit scratch/sample_plugin
```

`--vcs-ref HEAD` selects the checkout instead of the latest release tag, and
includes uncommitted changes. Keep generated projects under the ignored
`scratch/` directory.
