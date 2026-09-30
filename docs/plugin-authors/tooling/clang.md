# Clang tooling

Formatting and diagnostics use the project's `.clang-format`, `.clangd` and
`.clang-tidy` configuration.

## Compilation database

The plugin rule generates `compile_commands.json` at the project root after a
build, with commands exported for clangd. It describes the configured MO2
release.

## Format

```powershell
clang-format -i src/Plugin.cpp
```

## Run clang-tidy

With LLVM on PATH, run from the project:

```powershell
xmake check clang.tidy -f 'src/**.cpp'
```

Adjust the file pattern to match your sources. Check each supported MO2 release
when sources branch on `MOPK_MO2_VERSION`.
