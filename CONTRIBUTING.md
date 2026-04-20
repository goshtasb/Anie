# Contributing to Project Aegis / A.N.I.E.

Thanks for your interest in contributing! This project is open source under the [MIT License](LICENSE), and contributions of all kinds — bug reports, feature ideas, code, docs, tests — are welcome.

## Table of contents

- [Code of Conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Branching and commits](#branching-and-commits)
- [Pull request process](#pull-request-process)
- [Coding style](#coding-style)
- [Where to get help](#where-to-get-help)

## Code of Conduct

By participating in this project you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before your first contribution.

## Ways to contribute

- **Report a bug** — open a [Bug report](../../issues/new?template=bug_report.md). Include steps to reproduce, expected vs. actual behavior, and the component (backend, extension, mobile, site).
- **Request a feature** — open a [Feature request](../../issues/new?template=feature_request.md) describing the use case first, the solution second.
- **Improve detection accuracy** — false positives and false negatives in scan results are especially valuable. Include the URL scanned, the score/verdict returned, and what you think it should have been.
- **Improve docs** — fixes to [README.md](README.md) or [DOCUMENTATION.md](DOCUMENTATION.md) are always welcome.
- **Submit code** — pick an open issue (preferably one labeled `good first issue` or `help wanted`) or open an issue first to discuss larger changes.

## Development setup

See the [Quick start](README.md#quick-start) section of the README for per-component setup (backend, website, Chrome extension, mobile app).

You will need your own API keys for xAI, Tavily, Firecrawl, and a Supabase project to run the backend end-to-end. Unit tests in [aegis-backend/test_logic.py](aegis-backend/test_logic.py) do not require external keys.

## Branching and commits

- Fork the repo and create a feature branch from `main`: `git checkout -b feat/short-description` or `fix/short-description`.
- Keep branches focused — one logical change per PR.
- Write commit messages that explain **why**, not just **what**. Example:
  ```
  Tighten Quote Shield to avoid penalizing satire

  Articles reporting on toxic speech were being scored as High Manipulation
  when the toxic language was entirely quoted. Adjusting the Quote Attribution
  Protocol to require journalist endorsement before applying the penalty.
  ```
- Never commit secrets, `.env` files, or API keys. `.gitignore` should catch these — if you add a new secret file pattern, extend `.gitignore` in the same PR.

## Pull request process

1. Make sure `main` is up to date and rebase your branch if it has diverged.
2. Run the relevant tests and smoke-check the component you touched.
3. Update [DOCUMENTATION.md](DOCUMENTATION.md) if you change the API, DB schema, scoring algorithm, or add a new Synapse directive.
4. Open a PR against `main`. Fill out the PR template.
5. A maintainer will review. Expect feedback — small nits and questions are normal.
6. Once approved and CI is green (when CI exists), a maintainer will merge.

## Coding style

- **Python (backend):** follow the style already in [aegis-backend/](aegis-backend). Keep function names descriptive. Prefer small, composable functions over large ones.
- **JavaScript / TypeScript (extension, mobile, site):** match the existing style per folder. The Chrome extension uses vanilla JS; the mobile app uses TypeScript.
- **SQL:** schema changes go in [aegis-backend/supabase_schema.sql](aegis-backend/supabase_schema.sql) with a comment explaining the change.
- **Comments:** only when the *why* is non-obvious. Well-named identifiers should do the rest.

## Where to get help

- Open a [Discussion](../../discussions) for open-ended questions (once Discussions are enabled).
- Open an [Issue](../../issues) for bugs and concrete feature requests.
- For security issues, please follow [SECURITY.md](SECURITY.md) — **do not** open a public issue.

Thanks again for contributing.
