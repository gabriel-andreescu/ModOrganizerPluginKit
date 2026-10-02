# Contributing

See [Development](docs/maintainers/development.md) for the environment,
formatting and checks.

## Repository layout

| Directory    | Responsibility                                                          |
| ------------ | ----------------------------------------------------------------------- |
| `templates/` | Copier project files.                                                   |
| `xmake/`     | Addon rules, deployment and packaging.                                  |
| `addons/`    | Addon distribution recipe.                                              |
| `packages/`  | Library and API recipes, the beta SDK files and package-specific rules. |
| `python/`    | Python helpers and pytest integration.                                  |

Template documentation belongs in `docs/plugin-authors/template/` and links to
the independent rule and helper references in `docs/plugin-authors/tooling/`.
Contributor setup and checks belong in `docs/maintainers/`.

## Supported MO2 releases

The `mo2` option in [`xmake/includes/project`](xmake/includes/project/xmake.lua)
lists the supported releases. Its first entry is the default. Keep that list,
the uibase requires in
[`xmake/includes/native`](xmake/includes/native/xmake.lua), the `mo2-releases`
default in the [build workflow](.github/workflows/build.yml), the
[CI](.github/workflows/ci.yml) matrix and the documentation aligned.

Plugins build against the Qt shipped by the oldest supported release. Qt loads
plugins built against an older minor version. Raise the `qt6base` version when
that release is dropped.

## Package maintenance

Update source revisions, package versions and archive hashes together. Review
adaptations against the new source before retaining them. Preserve upstream
license and exception files in the installed package.

### uibase

The [package definition](packages/m/mo2-uibase/xmake.lua) installs a release's
headers and import library as `mo2-uibase <release>`.

Stable releases use MO2's published `Mod.Organizer-<release>-uibase.7z` asset.
Add its SHA-256 checksum under the release version.

MO2 publishes no SDK for betas. For a beta, create
`packages/m/mo2-uibase/<release>/` containing:

- `include/`: `uibase/include/` from the release's source archive, unchanged.
- `uibase.def`: the export names of the release's `uibase.dll`. The package
  creates the import library from it.

From a Developer PowerShell for Visual Studio, beside the release's
`uibase.dll`:

```powershell
$exports = dumpbin /nologo /exports uibase.dll
"LIBRARY uibase.dll`nEXPORTS" | Set-Content uibase.def
$exports | Select-String '^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]{8}\s+(\S+)' |
    ForEach-Object { "    $($_.Matches[0].Groups[1].Value)" } | Add-Content uibase.def
```

Remove the previous beta's directory and version when replacing it.

| Adaptation                                          | Releases    | Purpose                                                                   |
| --------------------------------------------------- | ----------- | ------------------------------------------------------------------------- |
| Export `include/uibase/game_features` as an include | 2.5.2       | `imoinfo.h` includes `game_feature.h` without its directory.              |
| Include `formatters/qt.h` from `versioning.h`       | 2.5.3 betas | `versioning.h` derives from the `QString` formatter without including it. |

Review each adaptation against a new release's headers before retaining it.

## Validate rule and package changes

Build, package and load a consumer for every supported release. Install the
local checkout as the consumer's addon with XMake's `--debugdir` option in an
isolated global directory, and register it as the consumer's package repository:

```powershell
$env:XMAKE_GLOBALDIR = Join-Path $PWD ".xmake/development"
xmake repo --add --global mopk C:/path/to/ModOrganizerPluginKit
xrepo install --addon -y --debugdir=C:/path/to/ModOrganizerPluginKit "mopk X.Y.Z"
xmake repo --add mopk C:/path/to/ModOrganizerPluginKit
xmake f -y --policies=package.requires_lock:n --mo2=2.5.2
xmake
xmake package
```

The source override installs uncommitted code under the requested version, so it
belongs in an isolated development cache. The project's repository takes
precedence over the one in `xmake.lua`, so recipes also come from the checkout.
Disabling the requires lock keeps `xmake-requires.lock` from pinning or
recording it. Reinstall the addon after rule changes, and a package after recipe
changes with `xmake require -f -y <package>`.

XMake records the checkout in `xmake-addons.lock` when the lock has no entry for
the requested version. Don't commit that lock. Once the version is released,
return the consumer to it from a new shell:

```powershell
xmake repo --remove mopk
Remove-Item xmake-addons.lock
xmake f -c -y
```

Run the [tests](docs/maintainers/development.md#tests) when changing the
generator, packaging, deployment or release workflows.

Deploy the DLL to each release's MO2 installation and check its log for load
errors. MO2 rejects plugins whose Qt metadata was built in debug mode or against
a newer Qt minor version than it ships.

## CI and releases

Unreleased work lands on `dev`. `main` tracks the latest release.

[CI](.github/workflows/ci.yml) runs the development checks and tests, and the
formatting checks on a generated project. When the addon, packages, template or
CI change, and on tags or manual runs, it builds a generated plugin for every
supported release and checks its Qt entry point and release metadata. CI cannot
load the plugin in MO2.

Keep the XMake version in the CI and consumer workflows aligned with
[the development setup](docs/maintainers/development.md#xmake).

For releases, update `python/pyproject.toml`, `uv.lock`, `mopk_version` in
`copier.yml` and the dated changelog entry. Add the version to
`addons/m/mopk/xmake.lua`. The template's `add_addons` version and build
workflow tag follow `mopk_version`, and CI fails when the package version,
`mopk_version` and the recipe disagree. Keep existing recipe versions so
consumers can continue installing older releases.

Merge `dev` into `main` through a pull request without squashing, then publish a
matching lightweight `vX.Y.Z` tag on `main` with `git tag vX.Y.Z`. Workflows
calling `build.yml` by an annotated tag cannot find its nested release workflow,
so CI rejects annotated release tags. The addon downloads that tag, and CI
publishes the source release after checks pass. Do not move published release
tags.

MOPK and [plugin releases](docs/plugin-authors/tooling/github-actions.md) share
[release.yml](.github/workflows/release.yml), which extracts notes with
[Changelog Reader](https://github.com/mindsers/changelog-reader-action).
