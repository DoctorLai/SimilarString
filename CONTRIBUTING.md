# Contributing to SimilarString

Bug fixes, tests, documentation, and scoped API improvements are welcome. For changes to the API
contract or deployment model, open an issue describing the use case first. Follow the
[code of conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately using
[SECURITY.md](SECURITY.md).

## Setup

Fork the repository, clone your fork, and create a working branch from the latest `main`. Use Python
3.12 or 3.13 and Node.js 22 or newer. In a Linux/macOS shell:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
npm test
```

Keep the virtual environment active when running npm commands: they call `python` from your PATH.
Node is a tooling dependency, not a requirement for the running API. The development requirements
omit PyTorch and SentenceTransformer so unit tests do not download models. To run the real service,
also follow the runtime installation instructions in [README.md](README.md).

Install Bash and jq to include the smoke-script regression tests in `npm test` and `npm run check`.
Those tests substitute a local curl stub, so they need neither Docker nor network access. They are
skipped when Bash or jq is unavailable; pytest lists the skipped tests in its summary.

## Before a Pull Request

```bash
npm run lint:fix
npm run format
npm run check
```

`check` runs formatting checks, Ruff, tests with branch coverage, independent 90% minimums for
statements, functions, and branches, and the runtime ZIP build. Fix uncovered behavior with useful
tests; do not lower the threshold or exclude executable paths to make a change pass. Tests live in
[tests/test_server.py](tests/test_server.py) and [tests/test_tooling.py](tests/test_tooling.py).

For API, dependency, startup, or Docker changes, also run:

```bash
npm run test:integration
```

This needs Docker with Compose v2, Bash, curl, jq, and network access to download the default model.
Tests create isolated containers and ports, clean up on exit, and verify real inference. CPU CI does
not validate CUDA deployments; include hardware-specific results when changing GPU behavior.

Each integration run starts with a fresh model cache. Allow the model to download and load before
expecting HTTP readiness, even when Docker reuses its image layers. For slower downloads, run
`SS_STARTUP_TIMEOUT=600 npm run test:integration`. The default is 300 seconds; the override also
sets Compose's healthcheck grace period. The Docker test prints a command for following live logs.

## Compatibility and Scope

- Preserve both `GET /` with a JSON body and `POST /`, response field names, and input
  normalization.
- Add regression tests for invalid input, cache behavior, or startup changes where applicable.
- Do not log submitted text or add an external inference service without an explicit design
  discussion.
- Keep configuration examples, policies, and API documentation consistent with behavior.
- Do not commit virtual environments, model weights, credentials, coverage output, or build
  archives.
- The runtime ZIP uses an explicit file allowlist. Update [scripts/project.py](scripts/project.py)
  when adding a required runtime file, and test the archive contents.

## Submitting

Open a pull request against `main` with the problem, behavior change, compatibility impact, and
commands you ran. Keep unrelated cleanup in a separate change. Maintainers may request changes
before merging; direct writes to protected branches are not needed.

CI publishes a coverage table to the job summary. Same-repository PRs also receive one bot comment,
updated on reruns when token permissions allow. Forks and Dependabot PRs use the summary only. No
coverage reports are uploaded as artifacts or sent to an external coverage service.

## Snapshot Versions

This service is not published to npm or PyPI. For a new user-facing snapshot, update
[VERSION](VERSION) with an ISO date (`YYYY-MM-DD`) and add an entry to [CHANGELOG.md](CHANGELOG.md).
Multiple changes for the same snapshot can share that date. The health endpoint and ZIP filename
read the same file.

Questions belong in [GitHub issues](https://github.com/DoctorLai/SimilarString/issues); see
[SUPPORT.md](SUPPORT.md) for the information needed to reproduce a problem.
