# ModOrganizerPluginKit

An opinionated toolkit for Mod Organizer 2 plugins, with project generation,
build rules, testing helpers and release workflows.

Use the [project template](docs/plugin-authors/template/projects.md), or
[add tools to an existing plugin](docs/plugin-authors/tooling/building.md). See
the [documentation](docs/README.md) for individual rules and helpers.

## Create a project

Requires [Copier](https://copier.readthedocs.io/en/stable/), Git and
[XMake 3.1.1 or newer](https://github.com/xmake-io/xmake/releases/tag/v3.1.1).

```powershell
copier copy https://github.com/gabriel-andreescu/ModOrganizerPluginKit.git my_plugin
```

[First build and project options](docs/plugin-authors/template/projects.md)

## Update a project

Requires a clean Git working tree and the project's `.copier-answers.yml`.

```powershell
copier update
```

[Updating build tools and dependencies](docs/plugin-authors/tooling/updating.md)

## Development

See [development setup](docs/maintainers/development.md) and
[contribution guidelines](CONTRIBUTING.md).

## License

[MIT](LICENSE)
