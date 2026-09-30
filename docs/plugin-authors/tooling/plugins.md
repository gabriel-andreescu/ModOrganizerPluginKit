# MO2 plugins

MOPK's plugin rule builds Qt plugin DLLs against uibase. See
[MO2 releases and dependency sources](dependencies.md) before choosing a
release.

## Target configuration

With [MOPK configured](building.md), include the native defaults:

```lua
includes("@addon/mopk/native")

target("Plugin")
    set_default(false)
    set_basename("my_plugin")
    set_version("1.2.0")
    add_rules("@addon/mopk/plugin")
    add_files("src/**.cpp", "src/**.h")
    add_packages("qt6base", "mo2-uibase")

target("my_plugin")
    set_version("1.2.0")
    add_rules("@addon/mopk/package", {targets = {"Plugin"}})
```

`native` requires uibase for the selected MO2 release and Qt. The plugin rule
links QtCore, QtGui, QtWidgets, QtNetwork and QtQuickWidgets, the modules uibase
exposes. Add further Qt modules with `add_frameworks`. List headers declaring
`Q_OBJECT` classes in `add_files` so moc processes them.

The native defaults select x64, `releasedbg`, the dynamic MSVC runtime and
C++23. They enable extra warnings as errors, UTF-8 source encoding and
compilation database generation. Select another mode with `xmake f -m`. MO2
ships release builds of Qt and rejects plugins built in `debug` mode.

Use `set_warnings("allextra")` on a target to retain extra warnings without
treating them as errors. An explicit `set_languages` also overrides C++23.

Use the same compiler defaults for test and utility targets:

```lua
add_rules("@addon/mopk/native.compiler")
```

Packages include the plugin's DLL and available debug symbols at the root of
MO2's `plugins/` directory. Building the plugin alone does not deploy or package
it.

## MO2 releases

Each build targets one MO2 release, `2.5.2` by default:

```sh
xmake f --mo2=2.5.3beta12
```

Each release builds in its own directory under `build/`, so switching releases
keeps incremental builds and never mixes objects compiled against different
uibase headers.

## Definitions

| Definition           | Value                                                        |
| -------------------- | ------------------------------------------------------------ |
| `MOPK_MO2_VERSION`   | Selected MO2 release as a string literal, such as `"2.5.2"`. |
| `MOPK_VERSION_MAJOR` | Major component of the target's `set_version`.               |
| `MOPK_VERSION_MINOR` | Minor component of the target's `set_version`.               |
| `MOPK_VERSION_PATCH` | Patch component of the target's `set_version`.               |

The version definitions are only present when the target sets a version.
