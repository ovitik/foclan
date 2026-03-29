# Foclan 1.0

Foclan is a compact LLM-first language for precise data transformation and exact JSON-like output shaping.

The core idea is simple: in vibecoding, not only the prompt and the model matter. The language itself is also a variable.

Most mainstream languages were optimized for human writing and reading. That does not automatically make them optimal for LLMs. Foclan explores the opposite direction: a language designed around what current LLMs tend to do well, while removing some of the things that are natural for humans but fragile for models.

This repository is the standalone public `Foclan 1.0` package. It contains:

- the installable `foclan` CLI
- the stable recommended dialect
- the packaged prompt bundle
- executable examples
- Codex and Cursor integration scaffolds

## Why Foclan Exists

Foclan is based on the hypothesis that LLM code quality can improve not only through:

- a better prompt
- a better model

but also through:

- a better language for the model

The current focus is not on replacing a general-purpose language. The focus is on giving LLMs a cleaner medium for:

- simple but exact data manipulation
- filtering, grouping, counting, sorting, and selection
- building precise JSON-like outputs
- preparing compact payloads for downstream API or LLM calls

## Why Foclan Can Be Easier For LLMs

Foclan tries to reduce some of the things that often make LLM-generated programs brittle:

- linear start-to-end flow
- one current value, `focus`, instead of many mutable variables
- minimal state tracking across distant parts of the program
- no traditional loops or recursion in the recommended style
- exact output shaping as a first-class concern
- compact syntax for the most common data tasks

The intended effect is:

- fewer syntax failures
- fewer logic mistakes in output shape
- shorter generated programs
- lower output token counts
- lower latency when the model uses the language well

## Benchmark Signals So Far

Foclan is still early, but the benchmark results are already interesting.

Selected internal results:

| Setup | Foclan | Python |
| --- | --- | --- |
| GPT-5-mini, minimal, main suite | 72.33% accuracy, 140.9 output tokens, 2.27s | 66.35% accuracy, 192.0 output tokens, 2.76s |
| GPT-5-mini, minimal, blind holdout | 68.14% accuracy, 158.4 output tokens, 2.42s | 59.80% accuracy, 211.6 output tokens, 2.89s |
| GPT-5.4 exploratory heavy sample, `Foclan none` vs `Python low` | 30.0% accuracy, 422.6 visible code tokens, 426.6 billed output tokens, 5.05s | 16.67% accuracy, 495.2 visible code tokens, 661.5 billed output tokens, 8.69s |

These are not universal claims. They are methodology-specific internal benchmarks. But they do suggest that for a meaningful class of hard transformation tasks, Foclan can already outperform Python on:

- accuracy
- visible code size
- billed output size
- end-to-end latency

## Important Tradeoffs

Foclan is not intended to be the nicest language for humans to write or read directly.

It is also not optimized for runtime execution efficiency in the way a mature general-purpose language is. The design target is LLM generation quality first, not raw execution speed of the produced programs.

There are also real current drawbacks:

- LLMs still have to learn Foclan from the prompt each time
- reasoning-capable models often overthink Foclan
- that overthinking can spend many hidden reasoning tokens
- Python still has a huge familiarity advantage from training data

The good news is that the Foclan prompt can be kept stable and cached well, so the prompt-learning overhead is not fully wasted every time. But it is still a real disadvantage today.

## What Foclan Is Trying To Become

The goal is not "a universal new programming language".

The goal is a stable and reasonably broad LLM-first language for:

- simple data work
- exact output shaping
- compact intermediate application logic
- practical coding with Codex, Cursor, and similar agent workflows

In other words: broad enough to be useful, but narrow enough to stay teachable and reliable.

## Install

Editable local install:

```bash
python -m pip install -e .[test]
```

Install directly from GitHub:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
```

Optional LLM extension:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-llm"
```

## Quickstart

```bash
foclan examples list
foclan examples validate
foclan examples run counts_dashboard
```

Start a new local project scaffold:

```bash
foclan init project
```

That writes:

- starter `programs/` and `inputs/`
- a project `README.md`
- `.env.example`
- `AGENTS.md`
- `.cursor/rules/foclan-v1.mdc`

Render the packaged prompt bundle:

```bash
foclan prompt
foclan prompt --anti-overthinking
```

## Optional LLM Extension

The core package stays general and elegant. Provider-specific functionality lives in the optional `foclan-llm` package.

`foclan-llm` adds:

- `.env` loading through `foclan run --dotenv`
- `call llm_text`
- `call llm_json`
- support for:
  - OpenAI Responses API
  - Anthropic Messages API
  - Google Gemini `generateContent` API

The extension is intentionally built on the current mainstream provider APIs rather than older legacy endpoints.

Install path:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-llm"
```

Inspect installed extensions:

```bash
foclan extensions list
```

Typical run:

```bash
foclan run programs/summarize.focus --env inputs.json --dotenv .env
```

Bundled LLM examples:

```bash
foclan examples list
foclan examples run openai_json_extract --dotenv .env
foclan examples run openai_text_summary --dotenv .env
```

Notes:

- `openai_json_extract` and `openai_text_summary` require `foclan-llm`
- for text calls, do not starve `max_output_tokens`; modern provider APIs may spend part of the budget on reasoning before final text

## Public Benchmark

Foclan now ships with a bundled public exact-output benchmark suite.

List the bundled suites:

```bash
foclan benchmark list-suites
```

Run a sampled benchmark against the default Python baseline:

```bash
foclan benchmark run \
  --provider openai \
  --model gpt-5-mini \
  --languages foclan python \
  --difficulties hard brutal super_brutal \
  --sample-size 20 \
  --seed 42 \
  --reasoning-effort none \
  --dotenv .env
```

The runner writes both JSON and Markdown reports.

Install note:

- benchmark runs need HTTP client + `.env` support
- easiest path is either `foclan-llm` or `foclan[benchmark]`

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
- [docs/BENCHMARK.md](docs/BENCHMARK.md)
- [prompt](prompt)
- [examples](examples)
- [templates](templates)
- [benchmarks](benchmarks)

## Product Boundary

This repository is intentionally narrow:

- yes: data manipulation, filtering, grouping, sorting, counting, exact response shaping
- yes: compact payload preparation for downstream LLM/API code
- no: general-purpose application programming
- no: experimental benchmark harnesses
- no: optimization/search benchmark branches

## Roadmap

The near-term plan is:

- stabilize one recommended Foclan dialect
- keep the language reasonably general, but focused on LLM-friendly data work
- reduce the amount of prompt teaching needed
- minimize output tokens and therefore latency
- maximize correctness in both syntax and logic
- improve real usability in Codex and Cursor workflows

Only after that foundation is stable should more specialized features be added.
