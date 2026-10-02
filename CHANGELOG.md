# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

### Added

- The build workflow installs npm dependencies for each committed
  `package-lock.json` before it runs pre-commit hooks.

### Changed

- The build workflow builds with XMake from `gabriel-andreescu/xmake` at a
  pinned commit instead of the XMake 3.1.1 release.

## [0.1.0] - 2026-09-30

### Added

- Initial release.
