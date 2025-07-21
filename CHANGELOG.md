# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.3.1] - 2023-11-06

## Added

- Added `CHANGELOG.md` to track changes to the project

### Fixes

- Fix issue where installer would install Python 3 packages when using Maya 2022 in Python 2 mode (#38).
- Fix installer failing because of an error installing PyYAML version 5.4.x (#38).

## [1.3.0] - 2023-09-11

### Added

- Now support Maya 2020, 2022, 2023 and 2024 (#36).
- Support downloading and importing Image Annotations as Blue Pencil layers Maya 2023+ (#36).
- Improved installer to leverage Maya module files (.mod) for easier install and future upgrades. Additionally, all dependencies are now contained within the install folder to not interfere with other tools/software on the computer (#36).
- Support Python 2 and 3 (#36).
- General code and stability improvements (#36).