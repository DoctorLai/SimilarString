# Changelog

User-facing changes are recorded by snapshot date. This repository does not publish an npm package,
PyPI distribution, or Chrome extension.

## 2026-09-22

### Fixed

- Integration startup waits explain cold model downloads without printing transient curl errors.
  Failed startup still reports diagnostics and exits nonzero.
- `SS_STARTUP_TIMEOUT` configures the startup budget for Docker and Compose tests; the default
  remains 300 seconds.

## 2026-09-21

### Added

- `POST /` alongside the existing `GET /` JSON API.
- `GET /health` with model, device, and the shared date-based version.
- JSON validation errors and a configurable request body limit, defaulting to 1 MiB.
- Bounded, thread-safe LRU embedding caching with a configurable entry limit per worker.
- Deterministic tests, a 90% coverage gate, and coverage summaries/eligible PR comments without
  uploads.
- npm commands for formatting, lint, tests, coverage, source ZIP builds, and complete offline
  checks.
- Contributor, security, support, privacy, and dependency-update policies.

### Changed

- Python 3.12 Docker base, non-root runtime, CPU PyTorch wheels by default, and a container health
  check.
- Compose v2 configuration with a persistent model cache and read-only configuration mount.
- Compose and helper scripts bind published ports to localhost by default. Set `SS_BIND_ADDRESS`
  explicitly for remote access behind appropriate protection.
- Default model precision is now `float32`; Flask debug mode is disabled by default.
- Application logs no longer include submitted sentences or response payloads.
- Runtime dependencies have version bounds; developer tools are pinned.

### Fixed

- Model precision is applied to the model instead of passing an unsupported `dtype` to `encode()`.
- Non-string JSON fields return `400` rather than raising an attribute error.
- Default configuration loading works from outside the repository directory; `SIMILARSTRING_CONFIG`
  selects another file.
- Docker tests check readiness and real GET/POST inference, use isolated resources, and clean up on
  failure.
- README request methods, JSON examples, startup commands, and test descriptions match the
  implementation.

Earlier changes are available in the
[commit history](https://github.com/DoctorLai/SimilarString/commits/main/).
