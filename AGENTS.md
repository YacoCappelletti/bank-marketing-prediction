# AGENTS.md

Guidelines for AI agents and contributors working on this repository.

## Commit convention (mandatory)

The owner versions the project with the commit history itself. Do not use
conventional-commit titles; follow this scheme exactly:

- **Commit title is only the project version**: `vX.Y.Z` (bump the patch level,
  e.g. `v0.0.2` -> `v0.0.3`).
- Put the human-readable summary and details in the **commit body**, separated
  from the title by one blank line.
- One version bump per change batch; do not create empty version commits.
- Do not rewrite published history except by explicit owner request.

Example:

```
v0.0.9

Document the commit-message convention in AGENTS.md.
```

## Project conventions

- Documentation and code comments in English.
- Python 3.13 with pinned dependencies in `requirements.txt`; work inside
  `.venv` (all Makefile targets handle this).
- Run `make test` before committing; the suite must stay green.
- Deterministic modeling: read the seed from `configs/model_config.json`, never
  hardcode paths or seeds; the test split is evaluated exactly once (G6).
- No raw PII values in logs or API error messages.
