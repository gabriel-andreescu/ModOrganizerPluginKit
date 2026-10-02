# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

### Added

- Generate only tooling configuration for an existing project with
  `tooling_only=true`.
- The build workflow installs npm dependencies for each committed
  `package-lock.json` before it runs pre-commit hooks.

### Changed

- The build workflow builds with XMake from `gabriel-andreescu/xmake` at a
  pinned commit instead of the XMake 3.1.1 release.

### Fixed

- The DevBench pytest session turns off MO2's Missing Masters check while tests
  run and restores it afterwards. MO2 could crash with heap corruption when
  tests refreshed it repeatedly.

## [0.1.0] - 2026-09-30

### Added

- Initial release.
