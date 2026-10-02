# Template defaults

See [the template's build choices](projects.md#what-the-template-selects) for
compiler defaults and packaged outputs.

## Editor and Git settings

Projects include `.editorconfig` and `.gitattributes` for consistent
indentation, LF line endings and binary files. VS Code settings recommend and
configure EditorConfig, XMake, Prettier, StyLua and the Lua language server,
along with clangd and, with DevBench tests, Python and Ruff. `.luarc.json` loads
the XMake declarations and plugin from
[xmake-luals](https://github.com/gabriel-andreescu/xmake-luals), which `xmake f`
installs into `.xmake/luals`.

## Formatting

Pre-commit formats staged files with:

- **Prettier:** Markdown (`.md`), YAML (`.yaml`, `.yml`) and JSON (`.json`,
  `.jsonc`), using [Prettier's defaults](https://prettier.io/docs/options) with
  `proseWrap: "always"`.
- **StyLua:** Lua (`.lua`), using four-space indentation.
- **Ruff**, when Python is included: lint fixes and formatting for `.py` and
  `.pyi` files. The lint configuration also enables import sorting.
- **clang-format:** C and C++ sources using the template's pinned
  [clang-format 23.1.0](../tooling/clang.md).

After initializing the project's Git repository, install the hooks with:

```powershell
uv tool install pre-commit
pre-commit install
```

Run formatting and lint fixes on all tracked files with
`pre-commit run --all-files`. CI runs the same hooks and fails if they change
files or report errors.

## Plugins

Projects include `.clang-format`, `.clangd` and `.clang-tidy`. The formatting
configuration requires clang-format 23 or newer. The clangd configuration uses
`clang-cl` for Windows x64 C++23. The clang-tidy header filter covers `src/`.
Adjust it if project headers live elsewhere. The generated plugin implements a
minimal `MOBase::IPlugin` reporting the target's
[version](../tooling/plugins.md#definitions) and precompiles the uibase and Qt
headers in `PCH.h`.

See [MO2 plugins](../tooling/plugins.md) and
[Clang commands](../tooling/clang.md).

## DevBench

`devbench_tests` adds Python dependencies and a startup test under `tests/mo2/`.
Install the dependencies with `uv sync`. See
[DevBench setup and pytest options](../tooling/devbench.md#python-setup) for
selecting an MO2 instance and running the suite.

`devbench_api` adds the [DevBench native API](../tooling/devbench.md#native-api)
to the plugin's dependencies. Both options are independent and can be added
through a Copier update.

## GitHub Actions

The generated workflow calls MOPK's
[reusable build workflow](../tooling/github-actions.md) on pushes to `main`,
pull requests and manual runs. Version tags also publish a GitHub release.
