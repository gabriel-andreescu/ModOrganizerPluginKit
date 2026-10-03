# Projects

Copier creates an MO2 plugin project.

## First build

Requires Git, Copier 9, XMake 3.1.1 or newer and Visual Studio 2022 with the C++
toolset and Windows SDK.

```powershell
copier copy --defaults -d project_name=my_plugin https://github.com/gabriel-andreescu/ModOrganizerPluginKit.git my_plugin
cd my_plugin
xmake f -y
xmake package
```

The ZIP at `build/dist/my_plugin/my_plugin-0.1.0-MO2-2.5.2.zip` contains
`my_plugin.dll` and its PDB. Extract it into an MO2 installation's `plugins/`
directory. To build for another MO2 release, configure it and package again:

```powershell
xmake f --mo2=2.5.3beta12
xmake package
```

To deploy while building, create `.xmake/mopk/deploy.json` with each release's
`plugins/` directory:

```json
{
  "my_plugin": {
    "2.5.2": ["C:/Tools/MO2/plugins"],
    "2.5.3beta12": ["C:/Tools/MO2-2.5.3beta12/plugins"]
  }
}
```

Run `xmake` and check `C:/Tools/MO2/plugins/my_plugin.dll`. See
[deployment](../tooling/packaging.md#deployment) for ownership and cleanup
behavior.

## Build a generated project

The generated `xmake.lua` registers MOPK and declares the plugin DLL and its
package. From the project root:

```powershell
xmake f -y
xmake
xmake package
```

Packages are written to `build/dist/<target>/`. See
[deployment and packaging](../tooling/packaging.md) for local deployment and
output paths, and [template defaults](defaults.md) for formatting and compiler
settings.

## What the template selects

- The plugin targets MO2 2.5.2 by default. Select another release with
  `xmake f --mo2=<release>`.
- The DLL uses x64, C++23, `releasedbg`, the dynamic MSVC runtime and extra
  warnings as errors. It builds against the uibase headers of the selected
  release and the Qt version MO2 2.5.2 ships.
- ZIPs contain the files that go into MO2's `plugins/` directory: the DLL and
  its PDB.

See [MO2 plugins](../tooling/plugins.md) for the compiler settings and
definitions, and [dependencies and MO2 releases](../tooling/dependencies.md) for
uibase and Qt.

## Options

Pass answers with `-d name=value`, or use the interactive prompts.

Set `tooling_only=true` to
[configure an existing project's tools](#tooling-for-existing-projects).

| Answer                               | Default     | Purpose                                                                                                                   |
| ------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------- |
| `project_name`                       | `my_plugin` | Project name, DLL basename and Qt plugin IID.                                                                             |
| `description`, `author`              | Empty       | Plugin metadata reported to MO2.                                                                                          |
| `pre_commit`                         | `true`      | Include [formatting and lint hooks](defaults.md#formatting).                                                              |
| `devbench_tests`                     | `false`     | Set up pytest with [MOPK's DevBench client and fixtures](../tooling/devbench.md#pytest).                                  |
| `devbench_api`                       | `false`     | Include the [DevBench native API](../tooling/devbench.md#native-api).                                                     |
| `deploy_2_5_2`, `deploy_2_5_3beta12` | Empty       | Initial [deployment](../tooling/packaging.md#deployment) destinations for each release, separated by `;`. Stored locally. |

Put source files in `src/`.

## Tooling for existing projects

Use the same template to add editor settings, formatter configuration and
pre-commit hooks to an existing project:

```powershell
copier copy https://github.com/gabriel-andreescu/ModOrganizerPluginKit.git C:/path/to/ExistingProject -d tooling_only=true
```

This mode generates only tooling configuration and `.copier-answers.yml`.
Sources, build files and documentation remain project-owned.

Review existing configuration files during the first copy. Keep project-specific
settings and hooks in those files. Later `copier update` runs merge template
changes with those customizations.

## Updating

Keep `.copier-answers.yml` in Git. From a clean working tree:

```powershell
copier update
```

Copier merges template changes with project edits. Review any merge conflicts.

Add further build or package targets directly in `xmake.lua`.

Copier updates project files. Use the separate
[tool and dependency update commands](../tooling/updating.md) to update the
installed build tools, Python dependencies or the reusable workflow.
