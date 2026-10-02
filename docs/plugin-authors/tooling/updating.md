# Updating tools and dependencies

| Part                        | Update                                                                       | Recorded in                                    |
| --------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| Generated project files     | `copier update`                                                              | `.copier-answers.yml` and the generated files. |
| XMake dependency recipes    | `xmake repo --update`                                                        | Local repository checkouts.                    |
| MOPK and xmake-luals addons | Change the `add_addons` version, then configure                              | `xmake.lua` and `xmake-addons.lock`.           |
| XMake dependencies          | `xmake require --upgrade`                                                    | `xmake-requires.lock`.                         |
| Python helpers              | `uv lock --upgrade-package modorganizer-plugin-kit`, then `uv sync --locked` | `uv.lock`.                                     |
| GitHub build workflow       | Change the `uses` release tag in the caller                                  | `.github/workflows/build.yml`.                 |

Keep `.copier-answers.yml`, `xmake-requires.lock`, `xmake-addons.lock` and
`uv.lock` in Git when the project uses them. Copier merges project files. It
does not reinstall build tools or update Python's environment.

## MOPK addon

Select the MOPK release in `xmake.lua`:

```lua
add_addons("mopk X.Y.Z")
```

The recipe installs the corresponding Git tag. XMake records the selected
version in `xmake-addons.lock` and keeps different versions side by side.

To upgrade, update the repository recipes, change the `add_addons` version and
configure again:

```powershell
xmake repo --update
xmake f -y
xmake package
```

MOPK releases select the supported MO2 releases, their uibase packages and the
Qt version. A release that drops an MO2 release no longer accepts it in `--mo2`.

## Library packages

`xmake-requires.lock` records resolved package versions, configurations and
repository revisions. `xmake require --upgrade` resolves within the project's
current declarations.

MOPK recipes can change their pinned source without changing the version label.
When adopting such a recipe change, reinstall the affected package, for example:

```powershell
xmake require --upgrade -f -y mo2-uibase
```

Review the lockfile changes and rebuild each MO2 release before publishing the
plugin.

## Workflow release

Use the MOPK release selected for the project in the reusable workflow's `uses`
reference. This selects CI's build steps, independently of the addon and
dependency installations. Copier updates that tag for generated projects. See
[workflow setup](github-actions.md#workflow-setup).
