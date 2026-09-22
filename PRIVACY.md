# Privacy

This document describes the SimilarString source application. It does not describe a public hosted
service or override the policies of whoever deploys it. Last updated: 2026-09-21.

## Submitted Text

The API receives `s1` and `s2`, computes embeddings locally, and returns the original strings and a
similarity score. It does not send these inputs to a hosted inference API or persist them in an
application database. Request data exists in process memory while the request is handled.

Embedding caching is disabled by default. When enabled, it retains normalized text keys and
embeddings in each worker's memory until eviction or process termination. The default limit is 1,024
entries per worker. Disable caching for sensitive workloads that should not retain text between
requests.

## Logs and Infrastructure

Application request-completion logs do not contain submitted text or response payloads. Web-server
access logs, reverse proxies, debugging tools, crash dumps, backups, and operator-added monitoring
may capture IP addresses, request metadata, or content. Operators are responsible for reviewing
those systems, defining retention periods, securing access, and meeting applicable obligations.

Use TLS and appropriate authentication before handling private text over a network. Do not enable
the Flask debugger in an exposed deployment. Follow [SECURITY.md](SECURITY.md).

## Downloads and External Services

Model initialization may contact Hugging Face to fetch model configuration, tokenizers, and weights.
Those services receive normal network metadata and the requested model identifier. Downloaded model
files are cached on disk; they are separate from the optional input embedding cache. Use a
provisioned local model or offline cache settings when network isolation is required.

The Docker image sets `HF_HUB_DISABLE_TELEMETRY=1`. Non-Docker operators can set the same
environment variable and should review their dependencies' telemetry and network behavior. Package
installation also contacts the configured Python/npm registries during setup, not as part of serving
a score.

The application has no browser interface, cookies, localStorage, analytics, or advertising code.
Repository badges, GitHub, and DeepWiki are external documentation services with their own policies.
CI coverage summaries contain source filenames and test coverage counts, not live API request data.

## Contact

Ask the operator of your deployed instance about access, retention, or deletion. For a privacy issue
in this codebase, contact [justyy@zoho.com](mailto:justyy@zoho.com); do not post private text in an
issue.
