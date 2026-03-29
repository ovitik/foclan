# Foclan 1.0

Foclan is a compact LLM-first language for precise data transformation and exact JSON-like output shaping.

This repository is the standalone public `Foclan 1.0` package. It contains:

- the installable `foclan` CLI
- the stable recommended dialect
- the packaged prompt bundle
- executable examples
- Codex and Cursor integration scaffolds

## Install

Editable local install:

```bash
python -m pip install -e .[test]
```

Install directly from GitHub:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
```

## Quickstart

```bash
foclan examples list
foclan examples validate
foclan examples run counts_dashboard
```

Render the packaged prompt bundle:

```bash
foclan prompt
foclan prompt --anti-overthinking
```

## Scaffold Editor Integration

In a target project where you want an LLM to write Foclan:

```bash
foclan init codex
foclan init cursor
```

That writes:

- `AGENTS.md` for Codex
- `.cursor/rules/foclan-v1.mdc` for Cursor

## Repository Layout

- [docs/SCOPE.md](docs/SCOPE.md)
- [docs/RECOMMENDED_DIALECT.md](docs/RECOMMENDED_DIALECT.md)
- [docs/INSTALL.md](docs/INSTALL.md)
- [docs/CODEX.md](docs/CODEX.md)
- [docs/CURSOR.md](docs/CURSOR.md)
- [prompt](prompt)
- [examples](examples)
- [templates](templates)

## Product Boundary

This repository is intentionally narrow:

- yes: data manipulation, filtering, grouping, sorting, counting, exact response shaping
- yes: compact payload preparation for downstream LLM/API code
- no: general-purpose application programming
- no: experimental benchmark harnesses
- no: optimization/search benchmark branches
