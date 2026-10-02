# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

## [0.2.0] - 2026-10-02

### Added

- Generate only tooling configuration for an existing project with
  `tooling_only=true`.
- The build workflow installs npm dependencies for each committed
  `package-lock.json` before it runs pre-commit hooks.

### Changed

- Generated projects pin xmake-luals 0.1.1, whose declarations match the XMake
  build the kits use.
- Native targets compile with `/Zc:__cplusplus`, so `__cplusplus` reports the
  selected standard.
- Generated README lists the documentation links and describes CI.
- Generated VS Code settings recommend and configure Prettier, StyLua and the
  Lua language server.
- The build workflow builds with XMake from `gabriel-andreescu/xmake` at a
  pinned commit instead of the XMake 3.1.1 release.

### Fixed

- The build workflow keeps separate compilation caches for different
  `configure-arguments`.
- DevBench instance discovery skips records left by MO2 processes that no longer
  run. Probing them could make a running MO2 miss the discovery timeout and be
  reported as not running.
- The DevBench pytest session turns off MO2's Missing Masters check while tests
  run and restores it afterwards. MO2 could crash with heap corruption when
  tests refreshed it repeatedly.

## [0.1.0] - 2026-09-30

### Added

- Initial release.
