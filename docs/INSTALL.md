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

## Verify

```bash
foclan examples list
foclan examples validate
foclan examples run counts_dashboard
```

## Prompt Bundle

```bash
foclan prompt
foclan prompt --anti-overthinking
foclan extensions list
```

## Project Scaffolding

```bash
foclan init codex
foclan init cursor
```
