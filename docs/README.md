# Documentation

## Plugin authors

Start with [the project template](plugin-authors/template/projects.md) for a
generated build setup, or
[use MOPK in an existing plugin](plugin-authors/tooling/building.md) to add
individual build rules or helpers.

### Project template

| Guide                                                    | Covers                                           |
| -------------------------------------------------------- | ------------------------------------------------ |
| [Projects](plugin-authors/template/projects.md)          | Copier options, first build and updates.         |
| [Template defaults](plugin-authors/template/defaults.md) | Generated configuration and formatting defaults. |

### Build tools and helpers

| Guide                                                                   | Covers                                                         |
| ----------------------------------------------------------------------- | -------------------------------------------------------------- |
| [Use MOPK in an existing plugin](plugin-authors/tooling/building.md)    | Integrating build rules and helpers without the template.      |
| [MO2 plugins](plugin-authors/tooling/plugins.md)                        | Target configuration, compiler defaults and definitions.       |
| [Dependencies and MO2 releases](plugin-authors/tooling/dependencies.md) | Supported releases, dependency sources and uibase adaptations. |
| [Deployment and packaging](plugin-authors/tooling/packaging.md)         | Package contents, local deployment and ZIPs.                   |
| [Clang tooling](plugin-authors/tooling/clang.md)                        | Compilation databases, formatting and lint commands.           |
| [GitHub Actions](plugin-authors/tooling/github-actions.md)              | Plugin builds and releases.                                    |
| [Nexus Mods](plugin-authors/tooling/nexus.md)                           | File destinations, categories and release uploads.             |
| [Updating](plugin-authors/tooling/updating.md)                          | Addon, dependency, Python and workflow updates.                |
| [DevBench](plugin-authors/tooling/devbench.md)                          | Python helpers, pytest fixtures, goldens and native API.       |

## MOPK maintainers

- [Development](maintainers/development.md): environment, formatting and tests.
- [Contributing](../CONTRIBUTING.md): repository layout, package maintenance and
  MOPK releases.
