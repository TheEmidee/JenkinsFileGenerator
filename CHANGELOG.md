# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/twisted/my-project/tree/main/changelog.d/>.

<!-- towncrier release notes start -->

## [1.9.2] - 2026-03-22

### Fixed

- Fixed crash inside the unreal feature when pre_tasks is not set ([#35](https://github.com/TheEmidee/JenkinsFileGenerator/issues/35))


## [1.9.1] - 2026-03-19

### Changed

- Updated the unreal feature to run Setup.ps1 from UEProjectBootStrap only when the jenkins job ID is different ([#33](https://github.com/TheEmidee/JenkinsFileGenerator/issues/33))


## [1.9.0] - 2026-01-27

### Removed

- Removed the pyscripts config from unreal ([#32](https://github.com/TheEmidee/JenkinsFileGenerator/issues/32))

### Added

- Added python feature ([#29](https://github.com/TheEmidee/JenkinsFileGenerator/issues/29))

### Changed

- Updated the archive feature to execute its scripts through the python feature ([#28](https://github.com/TheEmidee/JenkinsFileGenerator/issues/28))
- Updated the unreal feature to execute its scripts through the python feature ([#29](https://github.com/TheEmidee/JenkinsFileGenerator/issues/29))
- The unreal feature will sort the tasks of each parallel group alphabetically ([#31](https://github.com/TheEmidee/JenkinsFileGenerator/issues/31))

### Fixed

- Fixed an issue in the unreal feature which would not call `projectCheckout`
  Fixed an issue where failing to generate the buildgraph export file would not fail the jenkinsfile generation
  Fixed the properties feature which would not output anything in the final groovy ([#32](https://github.com/TheEmidee/JenkinsFileGenerator/issues/32))


## [1.8.0] - 2026-01-26

### Changed

- Updated the unreal feature to now pass arguments without using JSON strings
  Renamed the git additional function `checkout` to `projectCheckout` to avoid naming collision with the function from the jenkins git plugin ([#27](https://github.com/TheEmidee/JenkinsFileGenerator/issues/27))

### Fixed

- Fixed the git feature which would output garbage characters for the submodule options ([#27](https://github.com/TheEmidee/JenkinsFileGenerator/issues/27))
- Fixed the `archive` feature to now use PyScript's script aliases ([#28](https://github.com/TheEmidee/JenkinsFileGenerator/issues/28))


## [1.7.1] - 2026-01-22

### Changed

- Updated github actions to ease releasing the package
  Created `create_release` task ([#26](https://github.com/TheEmidee/JenkinsFileGenerator/issues/26))


## [v1.7.0] - 2026-01-18

### Added

- automatic semantic versioning ([#25](https://github.com/TheEmidee/JenkinsFileGenerator/pull/25))

## [v1.6.1] - 2026-01-17

### Added

- Distribution setup ([#21](https://github.com/TheEmidee/JenkinsFileGenerator/pull/21))
- Ruff mypy ([#23](https://github.com/TheEmidee/JenkinsFileGenerator/pull/23))
- Publish to pypi with github action ([#24](https://github.com/TheEmidee/JenkinsFileGenerator/pull/24))

## [v1.5.0] - 2026-01-17

### Added

- archive feature ([#10](https://github.com/TheEmidee/JenkinsFileGenerator/pull/10))
- add plasticscm feature ([#13](https://github.com/TheEmidee/JenkinsFileGenerator/pull/13))
- blackboard data ([#14](https://github.com/TheEmidee/JenkinsFileGenerator/pull/14))
- Added new batch mode which reads a batch YAML config file to generate multiple jenkinsfiles in one command ([#15](https://github.com/TheEmidee/JenkinsFileGenerator/pull/15))
- Features output customization ([#18](https://github.com/TheEmidee/JenkinsFileGenerator/pull/18))
- Ruff and mypy validation ([#20](https://github.com/TheEmidee/JenkinsFileGenerator/pull/20))

### Fixed
- unreal bug fixes by @TheEmidee in https://github.com/TheEmidee/JenkinsFileGenerator/pull/11
- unreal output properties in job by @TheEmidee in https://github.com/TheEmidee/JenkinsFileGenerator/pull/12

## [v1.0.0] - 2025-07-29

Initial release of the generator

