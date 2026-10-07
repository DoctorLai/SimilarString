# SimilarString

[![CI](https://github.com/DoctorLai/SimilarString/actions/workflows/ci.yaml/badge.svg)](https://github.com/DoctorLai/SimilarString/actions/workflows/ci.yaml)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Node tooling](https://img.shields.io/badge/Node.js%20tooling-%3E%3D22-339933?logo=nodedotjs&logoColor=white)](.nvmrc)
[![License](https://img.shields.io/github/license/DoctorLai/SimilarString)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-Ruff-D7FF64)](https://docs.astral.sh/ruff/)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![Last commit](https://img.shields.io/github/last-commit/DoctorLai/SimilarString/main)](https://github.com/DoctorLai/SimilarString/commits/main/)
[![Commit activity](https://img.shields.io/github/commit-activity/m/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/graphs/commit-activity)
[![Stars](https://img.shields.io/github/stars/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/stargazers)
[![Watchers](https://img.shields.io/github/watchers/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/watchers)
[![Forks](https://img.shields.io/github/forks/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/forks)
[![Open issues](https://img.shields.io/github/issues/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/issues)
[![Open PRs](https://img.shields.io/github/issues-pr/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString/pulls)
[![Repository size](https://img.shields.io/github/repo-size/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString)
[![Top language](https://img.shields.io/github/languages/top/DoctorLai/SimilarString)](https://github.com/DoctorLai/SimilarString)
[![Privacy](https://img.shields.io/badge/privacy-self--hosted-18794E)](PRIVACY.md)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/DoctorLai/SimilarString)

A self-hosted HTTP API for comparing the meaning of two sentences. SimilarString runs a
SentenceTransformer locally and returns cosine similarity, using Flask and Gunicorn. Use it for
paraphrase checks, duplicate detection, or comparing short text in an existing application.

The current snapshot version is in [VERSION](VERSION); changes are recorded in
[CHANGELOG.md](CHANGELOG.md). There is no browser UI, Chrome extension, or hosted public API.
Node.js is only used for contributor tooling.

## Quick Start

With Docker installed:

```bash
git clone https://github.com/DoctorLai/SimilarString.git
cd SimilarString
docker build -t similarstring .
docker run --rm --name similarstring -p 127.0.0.1:5000:5000 similarstring
```

The first startup downloads the configured model from Hugging Face. Wait until `/health` responds
before sending similarity requests. In another terminal:

```bash
curl --fail http://127.0.0.1:5000/health
curl --fail-with-body --header 'Content-Type: application/json' \
    --data '{"s1":"This is a Surface Studio Laptop","s2":"That is a car"}' \
    http://127.0.0.1:5000/
```

Illustrative response; the exact score depends on the model and precision:

```json
{
  "status": "success",
  "s1": "This is a Surface Studio Laptop",
  "s2": "That is a car",
  "score": 0.083
}
```

## API

| Endpoint      | Request                                           | Response                                                         |
| ------------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| `POST /`      | JSON object with non-empty strings `s1` and `s2`  | `200`, original strings and numeric `score`                      |
| `GET /`       | The same JSON body; retained for existing clients | Same response as POST                                            |
| `GET /health` | No body                                           | `200`, `status: "ok"`, snapshot `version`, `model`, and `device` |

Prefer POST: GET request bodies are not reliably forwarded by all clients and proxies. Text is
trimmed and lowercased before encoding; the response preserves the original strings. Cosine
similarity is theoretically between -1 and 1, subject to floating-point rounding. It is not a
probability or a percentage, and a useful matching threshold depends on your dataset.

Malformed JSON, non-object payloads, missing fields, non-string values, and whitespace-only strings
return `400` with `{"status":"error","message":"..."}`. Requests exceeding the configured byte limit
return a JSON `413` error. Other HTTP errors use Flask's default responses.

The legacy optional `test` field still bypasses inference and echoes its value as `score`. It exists
for compatibility with diagnostic clients. Do not treat caller-supplied test scores as model
results.

Health checks do not perform inference. A successful check confirms that this process has loaded its
model and can serve HTTP; it does not measure model quality or GPU health.

## Configuration

Edit [config.yaml](config.yaml), or set `SIMILARSTRING_CONFIG` to another YAML file. The default
file is resolved relative to the service, not your current directory. Restart the process after
changes.

| Setting                    | Shipped value             | Meaning                                                                |
| -------------------------- | ------------------------- | ---------------------------------------------------------------------- |
| `model.name`               | `paraphrase-MiniLM-L6-v2` | Hugging Face model identifier or local model directory                 |
| `model.device`             | `auto`                    | CUDA when available, otherwise CPU; explicit PyTorch devices also work |
| `model.precision`          | `float32`                 | `float32` or `float16`; half precision needs compatible hardware       |
| `cache.enabled`            | `false`                   | Cache normalized input text and embeddings in process memory           |
| `cache.max_size`           | `1024`                    | Maximum entries per worker; least-recently-used entries are evicted    |
| `server.host`              | `0.0.0.0`                 | Bind address inside the process/container                              |
| `server.port`              | `5000`                    | Internal HTTP port                                                     |
| `server.workers`           | `4`                       | Gunicorn worker processes; each has its own cache and memory budget    |
| `server.debug`             | `false`                   | Development debugger; never enable on an exposed service               |
| `server.max_request_bytes` | `1048576`                 | Maximum JSON request body size, in bytes                               |

With caching enabled, `cache.max_size` must be a positive integer; YAML booleans are not valid
sizes.

The shipped model targets English. For multilingual input, including simplified and traditional
Chinese, select a suitable model such as `paraphrase-multilingual-MiniLM-L12-v2` and evaluate it on
your own examples. JSON accepts Unicode, but that does not guarantee model accuracy in every
language. Models also truncate inputs beyond their tokenizer's maximum length.

## Docker Compose

Use Docker Compose v2:

```bash
docker compose up --build --detach --wait --wait-timeout 300
docker compose logs --follow flask-app
docker compose down
```

Compose mounts the configuration read-only and keeps downloaded models in a named volume. Normal
`down` preserves that volume; `down --volumes` removes the model cache. Set `HOST_PORT=8080` to
change only the published port. Keep the internal port at 5000 unless you also update the mapping.

Compose and the helper scripts publish to `127.0.0.1` by default. Set `SS_BIND_ADDRESS` explicitly
for remote access, with authentication, TLS, and rate limiting at a reverse proxy. The Python
service itself has no authentication; [SECURITY.md](SECURITY.md) covers deployment precautions.

The image runs as a non-root user and installs CPU PyTorch wheels by default. GPU deployments can
pass `--build-arg TORCH_INDEX_URL=...` with a compatible index from the
[PyTorch installation guide](https://pytorch.org/get-started/locally/) and run with `--gpus all`.
GPU operation requires an NVIDIA-enabled Docker host and is not exercised by the CPU CI checks.

Existing helpers remain available after `source ./setup-env.sh`: [build.sh](build.sh),
[run.sh](run.sh), [stop.sh](stop.sh), [restart.sh](restart.sh), and
[build-and-run.sh](build-and-run.sh). Set `SS_DOCKER_IMAGE`, `HOST_PORT`, or `FLASK_ENV` before
sourcing to override their defaults. The run helper stays attached to container output.

## Run Without Docker

Use Python 3.12 or 3.13. On Linux/macOS, for a CPU installation:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch>=2.6,<3'
python -m pip install -r requirements.txt
python server.py
```

This uses Flask's development server and the YAML host/port settings. Set `server.host` to
`127.0.0.1` for local-only use. To use Gunicorn on a supported Unix host:

```bash
FLASK_ENV=production python server.py
```

Model downloads need network access on first use. A cached or local model can run offline; see
[SUPPORT.md](SUPPORT.md). Reduce worker count if model copies exceed your memory budget.

## Development Checks

From a repository checkout, activate a Python virtual environment, install the lightweight test
dependencies, and use Node.js 22 or newer (`nvm use` reads [.nvmrc](.nvmrc)):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
npm run check
```

| Command                        | Purpose                                                                    |
| ------------------------------ | -------------------------------------------------------------------------- |
| `npm run format`               | Format Python with Ruff and Markdown/JSON/YAML with Prettier               |
| `npm run format:check`         | Check formatting without editing files                                     |
| `npm run lint`                 | Run Ruff checks, including imports                                         |
| `npm run lint:fix`             | Apply Ruff's supported automatic fixes                                     |
| `npm test`                     | Run deterministic unit tests without downloading a model                   |
| `npm run coverage`             | Run tests and require at least 90% for statements, functions, and branches |
| `npm run build`                | Validate Python syntax and create a runtime source ZIP under `dist/`       |
| `npm run check` / `npm run ci` | Check formatting, lint, coverage, and the runtime build                    |
| `npm run test:integration`     | Build and test Docker and Compose with the actual model                    |

The ZIP uses the date in [VERSION](VERSION). It contains runtime sources and policies, not installed
dependencies, model weights, or contributor tooling. It is not a Chrome Web Store package. Use a
repository checkout for development commands. Existing images are built with Docker, not npm.

Unit tests replace the ML boundary with deterministic doubles; container tests cover the real model.
Smoke-script regression tests also need Bash and jq; they use a local curl stub and skip if those
tools are missing. Check pytest's summary for skipped tests. Integration tests require Docker,
Compose v2, Bash, curl, jq, and network access:

```bash
./tests/integration-tests-docker.sh
./tests/integration-tests-docker-compose.sh
```

Each integration run uses a separate container/project and an ephemeral local port, then cleans up
its resources. Compose also removes the test project's locally built image. To smoke-test an already
running server, run `./test_ml_server.sh`; set `SS_URL` to select another address.

The integration tests use fresh model caches, so even a cached Docker image can require a model
download on each run. HTTP is unavailable until the model has loaded. The smoke script prints a
startup message and buffers transient curl errors; a failed startup prints diagnostics and exits
nonzero. The Docker test also prints a command for following the container's live startup logs.

The default startup retry budget is 300 seconds. For a slower download, increase it for both Docker
and Compose tests:

```bash
SS_STARTUP_TIMEOUT=600 npm run test:integration
```

CI checks Python 3.12 and 3.13 and runs both container tests. Coverage appears in the Actions job
summary and an updated bot comment on same-repository pull requests. Fork and Dependabot pull
requests receive the summary only because their tokens cannot write comments. Repository policy must
allow `pull-requests: write` for comments. Quality jobs have read-only tokens; a separate publisher
posts the comment without checking out PR code. No coverage artifacts or external coverage-service
uploads are configured. The dynamic repository badges above do not write to the protected main
branch.

## Project Policies

- [Contributing](CONTRIBUTING.md) and [Code of conduct](CODE_OF_CONDUCT.md)
- [Support and troubleshooting](SUPPORT.md)
- [Security reporting](SECURITY.md) and [Privacy](PRIVACY.md)
- [Changelog](CHANGELOG.md) and [MIT license](LICENSE)

## Support Development

- [Buy me a coffee](https://justyy.com/out/bmc)
- [Sponsor on GitHub](https://github.com/sponsors/DoctorLai)
- [Vote for my witness](https://steemyy.com/witness-voting/?witness=justyy&action=approve)
- [Set a witness proxy](https://steemyy.com/witness-voting/?witness=justyy&action=proxy)
