# Examples

This folder contains two kinds of examples:

- `current/`: examples that are valid in the packaged Foclan 1.0 runtime
- `future/`: reserved for later product-direction examples that are not implemented yet

For the installable product path, the current examples are also bundled into the `foclan` package and exposed through:

```bash
foclan examples list
foclan examples validate
foclan examples run counts_dashboard
```

Some current examples require the optional `foclan-llm` extension. Those show up in
`foclan examples list` with a `requires_extensions` field and can be run like:

```bash
foclan examples run openai_json_extract --dotenv .env
foclan examples run openai_text_summary --dotenv .env
```
