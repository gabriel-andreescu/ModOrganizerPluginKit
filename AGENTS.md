# AGENTS.md

ModOrganizerPluginKit provides shared build rules, dependencies and release
workflows for Mod Organizer 2 plugins. Use the
[documentation index](docs/README.md) for rule and package usage. Read
[CONTRIBUTING.md](CONTRIBUTING.md) for package maintenance and validation.

## Code and dependencies

- Keep changes scoped. Follow existing patterns before introducing helpers or
  abstractions. Avoid unrelated formatting, renaming and cleanup.
- Comments explain non-obvious constraints, invariants or workarounds. Do not
  restate the code or describe earlier implementations.
- Verify uibase behavior against the matching MO2 release. Distinguish upstream
  defects from MOPK packaging adaptations, and state what remains unverified.
- Keep vendored uibase headers byte-identical to their MO2 source archive. Adapt
  them during package installation.
- Handle failure paths as well as success. Downloads, extraction and packaging
  must clean up temporary resources and report enough context to diagnose
  errors.
- Pass untrusted GitHub Actions inputs to shell steps through environment
  variables, never direct expression interpolation into command text.

## Validation

- Run the checks relevant to the change before calling it complete. Do not rely
  on CI alone.
- Validate rule, package and template changes through a generated consumer for
  every supported MO2 release. Inspect the DLL's Qt plugin metadata, package
  contents and deployed files when those outputs change.
- Plugins must load in each supported MO2 release. A successful build does not
  establish that MO2 accepts the plugin.

## Commits

- Use Conventional Commits. Describe the problem and resulting behavior for a
  reviewer evaluating the current diff. Omit session history and Git mechanics.
- Fix failures from the pre-commit checks instead of skipping them.
