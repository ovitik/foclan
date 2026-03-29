# foclan-llm

`foclan-llm` is the optional extension package for calling common LLM APIs from Foclan.

It keeps the core `foclan` package small while adding:

- `.env`-backed API key loading
- `llm_text`
- `llm_json`
- OpenAI Responses API
- Anthropic Messages API
- Google Gemini `generateContent` API

Current provider targets:

- OpenAI: Responses API
- Anthropic: Messages API with `anthropic-version: 2023-06-01`
- Google: Gemini REST `v1beta/models/*:generateContent`

## Install

Install the base package first:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
```

Then install the extension package from the same repository:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-llm"
```

## CLI usage

```bash
foclan extensions list
foclan run program.focus --env inputs.json --dotenv .env
```

## Payload shape

The Foclan program should build a request record and then call:

```focus
call llm_text
```

or

```focus
call llm_json
```

Common request fields:

- `provider`: `openai`, `anthropic`, or `google`
- `model`: provider model name
- `input`: string or JSON-like object
- `system`: optional system instruction
- `temperature`: optional number
- `max_output_tokens`: optional integer
- `timeout_seconds`: optional number

Additional field for `llm_json`:

- `schema`: JSON Schema object

## Example

```focus
in request
call llm_json
out
```

with an input object like:

```json
{
  "request": {
    "provider": "openai",
    "model": "gpt-5-mini",
    "system": "Extract a person record.",
    "input": "Jane is 54 years old and lives in Prague.",
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
      },
      "required": ["name", "age"],
      "additionalProperties": false
    }
  }
}
```

## Practical Notes

- `llm_json` is usually the most reliable first thing to try.
- `llm_text` may need a higher `max_output_tokens` than the final visible answer suggests, because modern APIs can spend part of the budget before emitting the final text.
- If OpenAI or Gemini reports that generation stopped at the token limit, increase `max_output_tokens` in the request record.
