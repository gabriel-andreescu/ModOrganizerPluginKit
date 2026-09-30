# Nexus Mods

MOPK uploads release packages with the
[official Nexus action](https://github.com/Nexus-Mods/upload-action). Each MO2
release's package updates its own existing Nexus file:

```lua
target("my_plugin", function()
    set_version("1.0.0")
    add_rules("@addon/mopk/package", {
        targets = { "Plugin" },
        nexus = {
            game = "skyrimspecialedition",
            mod_id = "YOUR_UNIQUE_MOD_ID",
            files = {
                ["2.5.2"] = { file_id = "YOUR_FILE_ID", category = "main", primary = true },
                ["2.5.3beta12"] = { file_id = "YOUR_BETA_FILE_ID", category = "main" },
            },
        },
    })
end)
```

Create the mod page and upload each file once through Nexus. Copy its **Unique
Mod ID** and **File ID** from the Files tab's Advanced view or the file's edit
form. These are the API IDs, not the numbers in download URLs.

| Field    | Purpose                                                                 |
| -------- | ----------------------------------------------------------------------- |
| `game`   | Domain of the game hosting the mod page, as in its URL.                 |
| `mod_id` | Unique Nexus mod ID, as a string.                                       |
| `files`  | Nexus file for each MO2 release. Releases without an entry are skipped. |

| File field     | Default                       | Purpose                                                 |
| -------------- | ----------------------------- | ------------------------------------------------------- |
| `file_id`      | Required                      | Existing Nexus file ID, as a string.                    |
| `category`     | Required                      | `main`, `optional` or `miscellaneous`.                  |
| `primary`      | `false`                       | Main download that also updates the mod page's version. |
| `display_name` | `<package> for MO2 <release>` | Name shown in Nexus's Files tab.                        |
| `description`  | Empty                         | File description.                                       |

Each mod can have one primary Main file. Other files retain their own versions
without changing the mod page's version. Packages without `nexus` still appear
in the GitHub release.

## Workflow

Add a `NEXUSMODS_API_KEY` repository secret using your
[personal Nexus API key](https://www.nexusmods.com/settings/api-keys), then pass
it to MOPK's [build workflow](github-actions.md):

```yaml
with:
  publish-nexus: true
secrets:
  NEXUSMODS_API_KEY: ${{ secrets.NEXUSMODS_API_KEY }}
```

Tag releases upload the built ZIPs after the GitHub release succeeds. Previous
Nexus versions move to Old files. The workflow does not publish unpublished mod
pages.

## Changelogs and retries

Nexus receives the package's
[selected release notes](github-actions.md#target-changelogs) as plain entries,
preserving category labels and link destinations. Packages sharing a mod and
changelog version share one changelog, with repeated entries removed. The root
changelog uses the release tag version. A custom target changelog uses that
package target's version.

Rerun failed jobs to resume publication. MOPK skips file versions already
present on Nexus and posts only missing changelog entries. It does not replace
uploaded files with another ZIP under the same version. Upload and changelog
failures fail the workflow.

The official upload action is currently in beta.
