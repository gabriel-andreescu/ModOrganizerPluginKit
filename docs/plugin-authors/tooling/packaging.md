# Deployment and packaging

## Package composition

Each package selects build targets and files. Paths are relative to MO2's
`plugins/` directory:

```lua
target("my_plugin")
    set_version("1.2.0")
    add_rules("@addon/mopk/package", {targets = {"Plugin"}})
    add_installfiles("data/(**)", {prefixdir = "my_plugin"})
```

`targets` adds build dependencies and collects each listed target's installable
outputs. Transitive dependencies and targets added only with `add_deps` do not
ship. Outputs are applied in list order, followed by the package's own
`add_installfiles` mappings. Later mappings replace files at the same
destination.

| Option         | Default                           | Purpose                                                                |
| -------------- | --------------------------------- | ---------------------------------------------------------------------- |
| `targets`      | `{}`                              | Build targets whose installable outputs ship.                          |
| `package_name` | Target name without its namespace | ZIP filename before the version suffix.                                |
| `changelog`    | Root `CHANGELOG.md`               | [Release notes](github-actions.md#target-changelogs) for this package. |
| `nexus`        | Unset                             | [Nexus Mods destinations](nexus.md) for release uploads.               |

`.gitkeep` files are omitted.

## Deployment

Set destinations per MO2 release in the ignored `.xmake/mopk/deploy.json` file:

```json
{
  "my_plugin": {
    "2.5.2": ["C:/Tools/MO2/plugins"],
    "2.5.3beta12": ["C:/Tools/MO2-2.5.3beta12/plugins"]
  }
}
```

Use the MO2 installation's `plugins/` directory. Use full target names,
including namespaces. Paths are absolute or relative to the project root. Each
release accepts multiple destinations.

Building a package prepares its current files and deploys them to the
destinations of the configured MO2 release. Targets or releases without
destinations are not deployed. Disable deployment with `xmake f --deploy=n`.
Close MO2 before deploying, since it locks loaded plugins.

Rebuilds remove obsolete files previously deployed by that package. Packages
sharing a destination must have non-overlapping output paths. Conflicts with
another package or unowned files fail before deployment changes its
destinations.

Ownership records live in the ignored `.mopk/deployment.lua`, independently of
XMake's cache. After deleting `.xmake/`, restore `deploy.json` to resume
deployment to the same destinations.

Removing a destination leaves its deployed files in place. Keep `.mopk/` while
those files are deployed. If ownership records are lost, remove this project's
previously deployed files or choose an empty destination before deploying again.

## ZIP packages

```powershell
xmake package
xmake package my_plugin
```

ZIPs contain the same prepared files as deployment. Versions come from package
targets, and the name includes the configured MO2 release.

| Target             | Default ZIP path                                                   |
| ------------------ | ------------------------------------------------------------------ |
| `my_plugin`        | `build/dist/my_plugin/my_plugin-<version>-MO2-<release>.zip`       |
| `Tools::my_plugin` | `build/dist/Tools/my_plugin/my_plugin-<version>-MO2-<release>.zip` |

The default distribution directory follows XMake's build directory. Override it
with `xmake f --distdir=dist`. Changing the distribution directory leaves
earlier output in place.

Packaging replaces a target's ZIP for the configured release and removes its
older versions. ZIPs for other releases, other targets and unrelated files are
preserved. Empty packages produce no ZIP.

Use `set_default(false)` for packages that should build only when selected
explicitly.
