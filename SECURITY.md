# Security Policy

## Supported Code

Security fixes target the latest `main` branch. Historical snapshots are not maintained separately.
Update the source, Python dependencies, container base image, and model files regularly. Dependency
version ranges are not a complete lock of transitive packages.

## Report a Vulnerability

Use
[GitHub private vulnerability reporting](https://github.com/DoctorLai/SimilarString/security/advisories/new).
If private reporting is unavailable, email [justyy@zoho.com](mailto:justyy@zoho.com), the maintainer
contact also listed in the code of conduct. Do not open a public issue containing exploit details,
credentials, or private input data.

Include the affected commit or snapshot date, deployment mode, impact, and a minimal reproduction
with synthetic input. This is a volunteer-maintained project; there is no guaranteed response SLA.

## Deployment Boundaries

- The service has no built-in authentication, TLS, authorization, or rate limiting. Place it behind
  appropriate controls before exposing it to untrusted clients.
- The Python process defaults to listening on all interfaces. Docker examples, Compose, and helper
  scripts limit host publishing to localhost; changing `SS_BIND_ADDRESS` changes that boundary.
- Keep debug mode disabled on exposed deployments. Use Gunicorn rather than Flask's development
  server.
- Keep request-size limits and worker/cache counts within your memory and compute budget. Cache
  limits count entries, not bytes, and caches are separate in each worker.
- The compatibility-only `test` request field bypasses inference. Never trust its returned value as
  a model decision or use the similarity endpoint as an authorization check.
- Only load models and configurations you trust. The application does not enable
  `trust_remote_code`. Model downloads need outbound network access unless files are already
  local/cached.
- Review proxy and infrastructure logging. The application omits request text from its own logs, but
  surrounding systems may still capture it. See [PRIVACY.md](PRIVACY.md).

## CI Permissions

PR code is tested using `pull_request`, not a privileged `pull_request_target` checkout. Actions are
pinned to verified commit IDs and dependency updates are proposed through Dependabot. Only the
quality job requests PR-comment write permission; fork and Dependabot runs do not attempt comments.
No workflow commits generated files to `main` or uploads coverage data to a third-party service.
