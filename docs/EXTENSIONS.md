# Extensions

Foclan is designed around a small core and a growing extension ecosystem.

That is not a temporary compromise. It is the intended product architecture.

## Why Extensions Exist

The core language should stay:

- small
- teachable from prompt context
- token-efficient
- reliable for LLM generation

Many practical workflows still need more capability:

- LLM API calls
- file I/O
- HTTP requests
- future SQL access
- future schema validation

Those should usually be added as extensions, not as core syntax.

## Current Public Extensions

### `foclan-llm`

Purpose:

- call common LLM APIs from a Foclan workflow
- keep secrets in `.env`
- preserve a narrow, explicit request shape

Current surface:

- `llm_text`
- `llm_json`
- OpenAI Responses API
- Anthropic Messages API
- Google Gemini `generateContent`

### `foclan-io`

Purpose:

- deterministic local file and tabular I/O
- simple data-pipeline building blocks without changing the language core

Current surface:

- `read_text`
- `write_text`
- `read_json`
- `write_json`
- `read_jsonl`
- `read_csv`
- `write_csv`

### `foclan-http`

Purpose:

- deterministic HTTP requests as workflow steps
- simple JSON/text API access without provider-specific core syntax

Current surface:

- `http_get_json`
- `http_get_text`
- `http_post_json`
- env-backed auth headers

## Extension Design Rules

An extension is a good fit for Foclan when it does at least one of these:

- simplifies common LLM-written workflows
- reduces token count compared with ad hoc Python glue code
- reduces failure surface in exact-output tasks
- fits naturally into linear data or agent pipelines
- adds practical capability without forcing more syntax into the core language
- keeps inputs and outputs explicit and data-shaped

An extension is a bad fit when it:

- only wraps Python without adding useful structure
- introduces many competing idioms for the same thing
- bloats the prompt teaching burden
- makes the core language harder to explain
- encourages open-ended side effects by default
- effectively turns Foclan into a second general-purpose language

## Preferred Extension Style

The best extensions follow these principles:

- request in, result out
- explicit data shape
- deterministic behavior by default
- narrow surface area
- minimal magic
- easy to describe in a short prompt section

Good extension API shape:

- a small number of host functions
- records as inputs
- JSON-compatible outputs

Avoid:

- large object models
- many subtly different variants
- implicit global state
- extension-specific mini-languages that compete with Foclan itself

## Relationship To Bridges

Extensions and bridges solve different problems.

- **Extensions** add reusable host capabilities such as LLM calls, I/O, or HTTP.
- **Bridges** will provide controlled escape hatches into another runtime when a step is easier to express there.

As a rule:

- if a capability is stable, repeatable, and commonly useful, prefer an extension
- if a step is exceptional, custom, or hard to encode cleanly in Foclan, a bridge may be the better tool

See also [BRIDGES.md](BRIDGES.md).

Bridge runtimes follow a sibling architecture rather than being normal host-function extensions. The first public runtime package is `foclan-python`.
