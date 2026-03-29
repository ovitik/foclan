# Planned Provider Call Surface

These examples show the intended product direction for Foclan 1.0.

They are not implemented in the current runtime yet.

## Example: OpenAI call

```text
secret openai_key OPENAI_API_KEY
in question
llm openai.chat model="gpt-5.4" api_key=@openai_key
extract text
out
```

## Example: Claude call

```text
secret anthropic_key ANTHROPIC_API_KEY
in prompt
llm anthropic.messages model="claude-sonnet" api_key=@anthropic_key
extract text
out
```

## Example: Gemini call

```text
secret gemini_key GEMINI_API_KEY
in prompt
llm gemini.generate model="gemini-2.5-pro" api_key=@gemini_key
extract text
out
```

## Intent

The product direction is:

- read a named secret from `.env`
- call a provider through a narrow builtin
- return text or JSON through a small stable response surface

The language should not expose raw HTTP details unless there is a very strong reason.
