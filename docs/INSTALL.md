# Install

## Local Editable Install

```bash
python -m pip install -e .[test]
```

## Direct GitHub Install

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
```

## Optional LLM Extension

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-llm"
```

This extension adds:

- `.env` loading
- `llm_text`
- `llm_json`
- OpenAI Responses API
- Anthropic Messages API
- Google Gemini `generateContent`

## Optional I/O Extension

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-io"
```

This extension adds:

- `read_text`
- `write_text`
- `read_json`
- `write_json`
- `read_jsonl`
- `read_csv`
- `write_csv`

## Optional HTTP Extension

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-http"
```

This extension adds:

- `http_get_json`
- `http_get_text`
- `http_post_json`
- environment-backed headers such as `{"env": "API_TOKEN", "prefix": "Bearer "}`

## Optional SQL Extension

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-sql"
```

This extension adds:

- `sql_query`
- `sql_exec`
- SQLite-first `path` / `dsn` / `dsn_env` connection requests

## Optional Python Bridge Runtime

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-python"
```

This package registers the first bridge runtime:

- `python`

Inspect it with:

```bash
foclan bridges list
```

## Verify

```bash
foclan examples list
foclan examples validate
foclan examples run counts_dashboard
foclan extensions list
```

## Prompt Bundle

```bash
foclan prompt
foclan prompt --anti-overthinking
```

## Project Scaffolding

```bash
foclan init project
foclan init codex
foclan init cursor
```

`foclan init project` is the fastest path for a new user. It writes:

- `programs/`
- `inputs/`
- starter `.focus` programs
- starter JSON inputs
- `.env.example`
- `AGENTS.md`
- `.cursor/rules/foclan-v1.mdc`
