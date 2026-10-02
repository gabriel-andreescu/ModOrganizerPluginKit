# GitHub Actions

MOPK's reusable [build workflow](../../../.github/workflows/build.yml) builds
`releasedbg` packages for each MO2 release and uploads their ZIPs as Actions
artifacts. Tag pushes also publish a GitHub release.

## Workflow setup

Add `.github/workflows/build.yml`:

```yaml
name: Build and release

on:
  push:
    branches: [main]
    tags: ["v[0-9]*", "[0-9]*"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build:
    permissions:
      contents: write
    uses: gabriel-andreescu/ModOrganizerPluginKit/.github/workflows/build.yml@vX.Y.Z
```

| Input                 | Default                    | Purpose                                                                        |
| --------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| `project-directory`   | `.`                        | Directory containing the project's `xmake.lua` and `CHANGELOG.md`.             |
| `mo2-releases`        | `["2.5.2", "2.5.3beta12"]` | JSON array of MO2 releases to build.                                           |
| `run-tests`           | `false`                    | Run `xmake test` before packaging.                                             |
| `dist-directory`      | `build/dist`               | ZIP output directory relative to the project.                                  |
| `configure-arguments` | Empty                      | Additional XMake configure arguments, one per line.                            |
| `publish-nexus`       | `false`                    | Upload configured packages to [Nexus Mods](nexus.md) after the GitHub release. |

Builds use Windows, MSVC and the
[XMake build](https://github.com/gabriel-andreescu/xmake) pinned as
`XMAKE_COMMIT` in the workflow. Deployment is disabled.

Select the MOPK release used by the project. See [updating](updating.md) for the
separate workflow, addon and dependency pins.

If the repository has a root `.pre-commit-config.yaml`, the workflow runs its
checks before building.

The workflow caches XMake, dependency downloads, installed packages and
compilation results between runs.

On MSVC targets outside MOPK's native rules, use `set_symbols("debug", "embed")`
so cached objects retain their debug information.

## Releases

Push an `X.Y.Z` or `vX.Y.Z` tag matching a dated `## [X.Y.Z] - YYYY-MM-DD` entry
in `CHANGELOG.md`. The workflow attaches the ZIPs for every MO2 release and uses
that entry as the release notes.

### Custom builds

Call [release.yml](../../../.github/workflows/release.yml) after your own build
job, from a workflow that runs on tag pushes, to reuse publication without the
build workflow. Pass `artifacts` with the name pattern of the Actions artifacts
containing the ZIPs, and `metadata` with the pattern of those containing XMake's
`.xmake/mopk/packages/*.json` records. `project-directory` and `changelog`
locate the root changelog, and `expected-version` requires the tag to match.
Leave `artifacts` empty for a source release.

Actions artifacts retain the target folders, including namespace directories. In
GitHub releases, duplicate ZIP filenames receive the target path as a prefix,
with directory separators replaced by hyphens. The target name is omitted from
the prefix when the ZIP already starts with `<target>-`. For example,
`Tools/my_plugin/my_plugin-1.0.0-MO2-2.5.2.zip` becomes
`Tools-my_plugin-1.0.0-MO2-2.5.2.zip`. Unique ZIP filenames remain unchanged.

Missing, empty or undated entries block publication. Existing releases are not
overwritten.

Enable [Nexus Mods publication](nexus.md) to upload the same packages and their
changelogs after the GitHub release succeeds.

### Target changelogs

Targets use the root release entry unless they declare a separate changelog:

```lua
target("my_plugin_extras")
    set_version("1.1.0")
    add_rules("@addon/mopk/package", {
        targets = {"Extras"},
        changelog = "src/extras/CHANGELOG.md"
    })
```

The declared changelog supplies the entry matching the target version. Paths are
relative to the project root. Keep changelogs outside the paths selected by
`add_installfiles` unless they should also ship in the ZIP.

The release body starts with the root entry selected by the tag, followed by the
target entries under package-name and version headings. Targets sharing a
changelog entry share one section. A missing target entry blocks publication.
