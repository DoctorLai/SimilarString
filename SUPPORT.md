# Support

For bugs and feature requests, use
[GitHub issues](https://github.com/DoctorLai/SimilarString/issues). For security issues, follow
[SECURITY.md](SECURITY.md) instead. Support is community-based with no SLA; the repository does not
operate a hosted API service.

## Include in a Report

- Snapshot date from [VERSION](VERSION) or `/health`, and the Git commit when available.
- Operating system, Python version, Docker/Compose versions, and CPU/GPU deployment details.
- Relevant configuration with credentials and private paths removed.
- A minimal request using synthetic text, expected behavior, actual response, and sanitized logs.
- Whether the problem reproduces through Docker, Compose, or a local Python process.

## Troubleshooting

| Symptom                                  | Check                                                                                                                                                                                                                                                                          |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Connection reset/refused during startup  | The model must finish loading before `/health` becomes available. Integration tests use fresh model caches even when the image is cached. Follow the startup log command printed by the Docker test; use `SS_STARTUP_TIMEOUT=600 npm run test:integration` for slow downloads. |
| Download failure                         | Check outbound HTTPS, disk space, and model-cache permissions. Private models may need credentials configured through Hugging Face's supported mechanisms.                                                                                                                     |
| Port already in use                      | For Compose/helper scripts set `HOST_PORT=8080`; for `docker run`, change only the left side of the port mapping.                                                                                                                                                              |
| JSON `400`                               | Send a JSON object with two non-empty string fields, `s1` and `s2`. Prefer POST.                                                                                                                                                                                               |
| JSON `413`                               | Reduce the input or adjust `server.max_request_bytes` and the reverse proxy's limit deliberately.                                                                                                                                                                              |
| Unexpected scores                        | Check model language, input truncation, normalization, precision, and any `test` override. Scores are not probabilities.                                                                                                                                                       |
| GPU not selected                         | The stock Docker image uses CPU wheels. Use a compatible PyTorch CUDA index, NVIDIA container support, and the appropriate device configuration.                                                                                                                               |
| Out of memory                            | Reduce Gunicorn workers and cache size; check model size and input length.                                                                                                                                                                                                     |
| `npm` commands cannot import pytest/Ruff | Activate the virtual environment and install the development requirements before running npm.                                                                                                                                                                                  |
| No coverage bot comment                  | Check the job summary. Forks and Dependabot use read-only tokens; repository policy can also restrict PR-comment writes.                                                                                                                                                       |

For offline deployments, provision the model files first and point `model.name` at the local model
directory. Hugging Face also supports `HF_HUB_OFFLINE=1` for cache-only operation; it fails if
required files are missing. Compose preserves its downloaded model volume across ordinary restarts.

See [README.md](README.md) for startup commands and [CONTRIBUTING.md](CONTRIBUTING.md) for test
workflows.
