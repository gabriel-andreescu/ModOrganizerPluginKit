# Using MOPK in an existing plugin

MOPK's build rules require Git, Windows with an MSVC C++23 toolchain and
[XMake 3.1.1](https://github.com/xmake-io/xmake/releases/tag/v3.1.1) or newer.

## Setup

| Integration                                | Requirements                              | Adds to the project                                              |
| ------------------------------------------ | ----------------------------------------- | ---------------------------------------------------------------- |
| XMake build rules                          | XMake and an MSVC C++23 toolchain         | Plugin targets, packaging and optional deployment.               |
| [Python helpers](devbench.md#python-setup) | Python 3.11+, DevBench for MO2 operations | A Python dependency. Native integration is optional.             |
| [DevBench API](devbench.md#native-api)     | MOPK's build rules                        | The API header, its companion source and the Qt handler adapter. |

These integrations do not require Copier or its generated project layout.

A complete `xmake.lua`:

```lua
add_repositories("mopk https://github.com/gabriel-andreescu/ModOrganizerPluginKit.git")
add_addons("mopk X.Y.Z")
includes("@addon/mopk/project", "@addon/mopk/native")
set_policy("package.requires_lock", true)

target("Plugin")
    set_default(false)
    set_basename("my_plugin")
    set_version("1.0.0")
    add_rules("@addon/mopk/plugin")
    add_files("src/**.cpp", "src/**.h")
    add_packages("qt6base", "mo2-uibase")

target("my_plugin")
    set_version("1.0.0")
    add_rules("@addon/mopk/package", {targets = {"Plugin"}})
```

The root policy enables XMake's dependency lockfile. `project` declares the
`deploy`, `distdir` and `mo2` options. `native` selects the compiler defaults
and requires uibase for the selected MO2 release and Qt.

## Build and package

```sh
xmake
xmake package
```

The example writes `build/dist/my_plugin/my_plugin-1.0.0-MO2-2.5.2.zip`.

With no target named, `xmake` builds default targets and their dependencies.
Package rules add dependencies from their `targets` option. The plugin's
`set_default(false)` leaves build selection to its packages. It still builds
when a package needs it or when requested directly, for example with
`xmake build Plugin`.

See [MO2 plugins](plugins.md) for releases and compiler settings, and
[deployment and packaging](packaging.md) for outputs.
