# Foclan 1.0

Foclan is a compact LLM-first orchestration language for precise data transformation, exact JSON-like output shaping, and agent-friendly workflow steps.

The core idea is simple: in vibecoding, not only the prompt and the model matter. The language itself is also a variable.

Most mainstream languages were optimized for human writing and reading. That does not automatically make them optimal for LLMs. Foclan explores the opposite direction: a language designed around what current LLMs tend to do well, while removing some of the things that are natural for humans but fragile for models.

This repository is the standalone public `Foclan 1.0` package. It contains:

- the installable `foclan` CLI
- the stable recommended dialect
- the packaged prompt bundle
- executable examples
- Codex and Cursor integration scaffolds

## The Story

Most people working with vibecoding currently optimize two things:

- the prompt
- the model

Foclan is built around a third variable:

- the language the model is asked to think in

That is the core bet behind the project.

Human-oriented languages like Python are excellent for human authors. But an LLM is not a human author. It is a token predictor with strong priors, limited working memory, and a tendency to overbuild code when the language gives it too many degrees of freedom.

Foclan tries to answer a narrow but important question:

> What if the language itself was designed to make LLM-generated programs shorter, more exact, and less brittle?

That is why Foclan is intentionally biased toward:

- linear start-to-end flow
- exact output shaping
- very small state surface
- fewer moving pieces per program
- compact solutions that are easy to validate

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
- orchestrating narrow agent steps in a predictable way

The updated product direction is:

- keep the core language extremely small and LLM-optimized
- add practical capability through extensions
- and eventually allow controlled bridging into other languages when Foclan is not the right expression tool for a step

## Why A Developer Might Actually Care

The pitch is not "learn another language for everything."

The pitch is:

- use Python, TypeScript, or your normal stack for application code
- use Foclan where LLMs most often fail: exact intermediate data programs

In practice that means Foclan is most interesting for the part of an AI workflow where a model has to write a small but exact transformation program and where "almost correct" is still wrong.

It is not trying to replace the rest of your stack. It is trying to become the best narrow language for:

- exact data workflow
- LLM-first glue code
- agent pipeline steps
- compact transformation layers between systems

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

## Best Use-Cases

The best current use-cases are the ones where Python is expressive for humans but too open-ended for LLMs.

Good current fits:

- exact JSON response shaping
- nested report building from multiple inputs
- filtering, counting, grouping, sorting, and top-selection
- provider payload assembly before downstream API calls
- schema-driven extraction pipelines
- deterministic glue code between raw inputs and structured outputs
- small "dashboard" style programs where key names and nesting must be exact
- LLM extraction followed by deterministic cleanup and reshaping
- compact orchestration steps inside larger agent workflows
- data pipelines where the output contract matters more than general-purpose expressiveness

Typical places where LLMs often do worse in Python than in Foclan:

- they add extra wrapper objects like `report`, `summary`, or `result`
- they return the right data under the wrong key names
- they overuse helper variables and drift away from the requested output shape
- they overengineer simple transforms into longer code with more failure surface
- they make local logic mistakes while juggling state across multiple intermediate variables
- they write plausibly correct code that is still structurally wrong for downstream systems

Foclan is especially promising when the real target is not "general coding" but:

- "return exactly this object"
- "compose these few inputs into this exact contract"
- "make the LLM stop improvising structure"

In other words, Foclan is best thought of as:

- a language for linearly transforming data
- a language for shaping exact outputs
- a language for orchestrating narrow steps in LLM-heavy workflows

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

Foclan also depends heavily on having good extensions for practical workflows. That is a feature of the architecture, not an accident: the core stays small on purpose.

The good news is that the Foclan prompt can be kept stable and cached well, so the prompt-learning overhead is not fully wasted every time. But it is still a real disadvantage today.

## Why Give Foclan A Chance

If you are already using Codex, Cursor, Claude Code, or similar tools, Foclan is worth trying for at least three reasons:

- it gives you a concrete way to trade language design against prompt complexity
- it can make exact-output tasks more reliable than plain Python
- it creates a benchmarkable, inspectable middle layer between raw model generation and production code

Even if you never adopt it broadly, Foclan is useful as an experiment in a question that is becoming increasingly practical:

> if agents are writing the code, should we keep assuming the optimal language is the same one humans preferred?

## What Foclan Is Trying To Become

The goal is not "a universal new programming language".

The goal is a stable and reasonably broad LLM-first language for:

- simple data work
- exact output shaping
- compact intermediate application logic
- practical coding with Codex, Cursor, and similar agent workflows
- data and agent orchestration where each step should stay easy for an LLM to generate correctly

The guiding idea now is:

- Foclan core handles the parts that benefit from being highly constrained
- extensions add practical power without bloating the core
- bridges will eventually provide controlled escape hatches into other runtimes such as Python

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

Optional local I/O extension:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-io"
```

Optional HTTP extension:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-http"
```

## Extension Philosophy

Foclan is intentionally split into:

- a very small core language
- optional extension packages
- and, in the future, bridge runtimes into other languages

Extensions make sense when they do at least one of these:

- simplify common LLM-written workflows
- reduce token count compared with handwritten Python glue code
- reduce failure surface for exact-output tasks
- fit naturally into linear data or agent pipelines
- add practical capability without forcing more syntax into the core language

Extensions do **not** make sense when they:

- only wrap Python without adding structure or reliability
- introduce many competing idioms
- bloat the prompt teaching burden
- turn Foclan into a second general-purpose language

See also:

- [docs/EXTENSIONS.md](docs/EXTENSIONS.md)
- [docs/BRIDGES.md](docs/BRIDGES.md)

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

## Optional I/O Extension

`foclan-io` adds small deterministic file I/O helpers without changing the language core.

It currently provides:

- `read_text`
- `write_text`
- `read_json`
- `write_json`
- `read_jsonl`
- `read_csv`
- `write_csv`

Install path:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-io"
```

Typical use:

```text
in request
call read_json
out
```

or:

```text
in request
call write_csv
out
```

The host function request is just normal data. For example:

```json
{
  "request": {
    "path": "outputs/report.json",
    "content": {"ok": true}
  }
}
```

## Optional HTTP Extension

`foclan-http` adds a very small deterministic HTTP layer as an extension, not as core syntax.

It currently provides:

- `http_get_json`
- `http_get_text`
- `http_post_json`

Install path:

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-http"
```

Typical use:

```text
in request
call http_get_json
out
```

Headers can be passed directly or backed by environment variables:

```json
{
  "request": {
    "url": "https://api.example.com/items",
    "headers": {
      "Authorization": {"env": "API_TOKEN", "prefix": "Bearer "}
    }
  }
}
```

This keeps secrets in `.env` and out of the `.focus` program itself.

## Available Extensions

Current public extensions:

- `foclan-llm`
  Adds `.env`-backed `llm_text` and `llm_json` calls for OpenAI, Anthropic, and Google.
- `foclan-io`
  Adds deterministic local text, JSON, JSONL, and CSV file operations.
- `foclan-http`
  Adds minimal deterministic JSON/text HTTP GET and JSON POST calls.

The intent is not to accumulate random plugins. The intent is to build an ecosystem of extensions that strengthen Foclan specifically for LLM-first data and agent workflows.

## Bridging To Other Languages

The likely next major core evolution is **bridging**.

The idea is simple:

- keep Foclan small and optimized for the things it does well
- and provide a controlled escape hatch when a step is better expressed in another language

In practice that means a future Foclan program may be able to:

- stay mostly in Foclan for exact shaping and orchestration
- hand the current `focus` to another runtime such as Python for one narrow step
- then return to Foclan with the new `focus`

This changes the role of Foclan in an important way:

- Foclan does not need to become fully general-purpose
- it only needs to be excellent at the LLM-friendly center of the workflow
- and good at handing off the rest in a controlled, low-friction way

See the early design direction in [docs/BRIDGES.md](docs/BRIDGES.md).

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
- [docs/EXTENSIONS.md](docs/EXTENSIONS.md)
- [docs/BRIDGES.md](docs/BRIDGES.md)
- [docs/BRIDGE_SPEC.md](docs/BRIDGE_SPEC.md)
- [docs/CODEX.md](docs/CODEX.md)
- [docs/CURSOR.md](docs/CURSOR.md)
- [docs/BENCHMARK.md](docs/BENCHMARK.md)
- [docs/FUTURE_CAPABILITIES.md](docs/FUTURE_CAPABILITIES.md)
- [prompt](prompt)
- [examples](examples)
- [templates](templates)
- [benchmarks](benchmarks)

## Product Boundary

This repository is intentionally narrow:

- yes: data manipulation, filtering, grouping, sorting, counting, exact response shaping
- yes: compact payload preparation for downstream LLM/API code
- yes: extension-driven capability for file, HTTP, LLM, and future SQL/schema workflows
- yes: future controlled bridging to other runtimes
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
- expand capability primarily through extensions
- introduce bridging only if it clearly improves expressiveness without hurting the core simplicity

Only after that foundation is stable should more specialized features be added.

See also:

- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/FUTURE_CAPABILITIES.md](docs/FUTURE_CAPABILITIES.md)
