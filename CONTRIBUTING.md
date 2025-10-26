<!-- SPDX-License-Identifier: MPL-2.0 -->
# Contributing

Thank you for your interest in contributing to Lousa Assurance!

## Licensing of Contributions

By contributing to this project you agree that your contributions are licensed under
the [Mozilla Public License 2.0](LICENSE) using inbound=outbound terms. Include the
`SPDX-License-Identifier: MPL-2.0` header in new source files and retain any existing
copyright notices.

## Getting Started

1. Run `make bootstrap` to create the local virtual environment, install
   dependencies, and set up pre-commit hooks.
2. Copy `.env.example` to `.env` and provide values for any required variables.
3. Explore the project structure described in `README.md`.

## Development Workflow

- Use the scripts in `scripts/` or the corresponding `make` targets for
  day-to-day tasks. `make check` mirrors the CI pipeline.
- Follow the [Conventional Commits](https://www.conventionalcommits.org/) style
  when crafting commit messages. A commit template is installed as part of the
  bootstrap process.
- Add or update tests alongside code changes. Unit tests belong under
  `tests/unit`, integration tests under `tests/integration`, and end-to-end
  scenarios in `tests/e2e`.
- Run `make lint fmt typecheck test` before pushing changes.

## Code Review

All changes should be submitted through pull requests. At least one code owner
must approve changes touching protected paths defined in `.github/CODEOWNERS`.

## Reporting Issues

Please use the issue tracker and include reproducible steps, expected behavior,
actual behavior, and environment details.

## Releasing

The release process is orchestrated through `scripts/release`, which aligns with
semantic versioning and updates `CHANGELOG.md` automatically.
