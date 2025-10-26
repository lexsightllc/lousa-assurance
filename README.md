<!-- SPDX-License-Identifier: MPL-2.0 -->
# Lousa Assurance

Lousa Assurance evaluates temporal and epistemic assurance cases defined in a
YAML-based DSL. The toolkit provides a Typer-powered CLI for parsing claims,
computing evidence of interest, and emitting provenance-rich results suitable
for audits and notebook exploration.

## Project Structure

```
.
├── assets/               # Static assets (images, diagrams)
├── ci/                   # CI/CD pipeline configuration snippets
├── configs/              # Configuration overlays and templates
├── data/                 # Sample data sets (non-sensitive)
├── docs/                 # Documentation, ADRs, and system maps
├── examples/             # Reference assurance cases
├── infra/                # Infrastructure-as-code entry points
├── notebooks/            # Exploratory Jupyter notebooks
├── sbom/                 # Generated software bill of materials
├── scripts/              # Cross-platform developer task shims
├── src/lousa/            # Python package with domain logic
├── tests/                # Unit, integration, and e2e tests
└── project.yaml          # Repository metadata contract
```

## Environment

- Python 3.11 (managed via `.tool-versions` or any direnv-compatible tool)
- Optional: Docker for containerized workflows via `docker-compose.yml`

Copy `.env.example` to `.env` and customize values before running workflows that
require environment variables.

## Developer Tasks

Each task is available through a script in `scripts/` and a corresponding Make
target. Commands are non-interactive and respect the `VENV_PATH` environment
variable (defaults to `.venv`).

| Task | Script | Make Target | Description |
| ---- | ------ | ----------- | ----------- |
| Bootstrap | `scripts/bootstrap` | `make bootstrap` | Create/update the virtual environment, install dependencies, and configure pre-commit/commit-msg hooks. |
| Developer server | `scripts/dev` | `make dev` | Launch the Typer CLI for rapid experimentation (pass CLI arguments as needed). |
| Lint | `scripts/lint` | `make lint` | Run Ruff (lint), Black (check), and isort (check). Use `--fix` to auto-correct. |
| Format | `scripts/fmt` | `make fmt` | Apply Black, isort, and Ruff formatting to the codebase. |
| Type check | `scripts/typecheck` | `make typecheck` | Execute mypy in strict mode. |
| Unit & integration tests | `scripts/test` | `make test` | Run pytest with coverage for unit and integration suites. |
| End-to-end tests | `scripts/e2e` | `make e2e` | Execute e2e scenarios (no-op when none are defined). |
| Coverage gate | `scripts/coverage` | `make coverage` | Generate XML/HTML reports and enforce adaptive line/branch thresholds with regression detection. |
| Build | `scripts/build` | `make build` | Produce source and wheel distributions. |
| Package | `scripts/package` | `make package` | Alias for build artifacts (for compatibility with downstream tooling). |
| Release | `scripts/release` | `make release` | Perform a semantic version bump and publish-ready artifacts. |
| Update dependencies | `scripts/update-deps` | `make update-deps` | Check for outdated dependencies and stage grouped updates. |
| Security scan | `scripts/security-scan` | `make security-scan` | Run dependency, SAST, and secret scans. |
| SBOM | `scripts/sbom` | `make sbom` | Generate a CycloneDX SBOM into `sbom/`. |
| Docs | `scripts/gen-docs` | `make gen-docs` | Build static documentation via MkDocs. |
| Migrations | `scripts/migrate` | `make migrate` | Run deterministic data/schema migrations (no-op currently). |
| Clean | `scripts/clean` | `make clean` | Remove build artifacts, caches, and the virtual environment. |
| Check | `scripts/check` | `make check` | Composite target running lint, typecheck, tests, coverage, and security scans. |

## Continuous Integration

GitHub Actions executes `make check` across Python 3.10 and 3.11 on Linux and
macOS. Caches are warmed for pip downloads and `.venv` contents. Coverage
reports, SBOM artifacts, and build outputs are uploaded for inspection. Release
signing and SBOM publication use Sigstore and CycloneDX workflows.

## Documentation & ADRs

Architectural decisions are documented under `docs/adr/`. New proposals should
follow the MADR template introduced in ADR 0001. Diagrams may be expressed in
Mermaid or PlantUML and committed alongside the ADRs.

## Observability

Structured logging is provided through `lousa.logging`, which configures
`structlog` with JSON output and automatic trace propagation. Downstream
integrations should enrich context with request IDs, user identifiers
(hashed/anonymized), and trace correlation metadata when embedding the library
into services.

## License

Lousa Assurance is licensed under the [Mozilla Public License 2.0](LICENSE). The MPL
requires that any distributed modifications to MPL-covered source files remain under
the same license, while larger works that merely incorporate this project may continue
under their own terms. Refer to the [NOTICE](NOTICE) file for attribution details and
redistribution requirements.

## Credits

- Project leadership and stewardship: Augusto "Guto" Ochoa Ughini
- Core contributors: the Lousa Assurance engineering team and community members

Please retain both the MPL-2.0 license and the NOTICE file when redistributing the
software.
