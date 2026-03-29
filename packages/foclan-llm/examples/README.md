# foclan-llm examples

These examples show the intended request shape for the optional LLM extension.

Run them with:

```bash
foclan run programs/openai_text.focus --env inputs/openai_text.json --dotenv .env
foclan run programs/openai_json.focus --env inputs/openai_json.json --dotenv .env
```

The same program shape works for Anthropic and Google by changing:

- `provider`
- `model`
- `.env` API key
