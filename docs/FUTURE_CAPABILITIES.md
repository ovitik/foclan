# Future Capabilities

This document collects the most promising next capabilities for Foclan.

The rule is simple:

- keep the core language small
- add capability through extensions first
- only expand the core when the gain is clear
- use bridges instead of core growth when another runtime is the cleaner answer

## Design Principles

New capabilities should improve at least one of:

- exactness of generated programs
- token efficiency
- latency
- teachability from prompt context
- practical usefulness in AI application workflows

They should not add large amounts of:

- new syntax variance
- provider-specific complexity in the core language
- human-only convenience at the cost of LLM reliability
- arbitrary general-purpose power when an extension or bridge would be cleaner

## Highest-Value Product Features

### 1. Public benchmark evolution

The public benchmark runner now exists. The next steps are:

- repeats
- blind subset mode
- side-by-side per-language delta tables
- charts from the CLI
- cached prompt reporting per provider when exposed

This is high value because it makes Foclan measurable rather than just arguable.

### 2. Project-level test command

Add something like:

```bash
foclan check
```

for validating all `.focus` files in a project and optionally running local fixture cases.

Why it matters:

- gives teams a very short feedback loop
- makes Foclan feel more like a real toolchain
- helps catch syntax and shape mistakes before LLM-generated code is committed

### 3. First-class fixture-based examples

Add a tiny convention for:

- `programs/*.focus`
- `inputs/*.json`
- `expected/*.json`

Then expose:

```bash
foclan test
```

This would be very compelling for exact-output workflows.

### 4. Built-in benchmark starter packs

Let users run:

```bash
foclan benchmark run --provider openai --model gpt-5-mini
```

but also:

```bash
foclan benchmark run --preset smoke
foclan benchmark run --preset hard
```

This would make the benchmark much easier to use and compare.

## Best Extension Directions

These should stay outside the core language.

### 5. `foclan-llm` expansion

Good next additions:

- provider/model presets
- provider capability introspection
- better structured-output defaults
- clearer token-limit diagnostics
- optional retry with the same request payload

### 6. `foclan-io` evolution

`foclan-io` now exists in first form. The next steps are:

- directory batch processing
- stdin/stdout helpers
- better CSV typing conventions
- path convenience helpers that still keep the core language clean

This is valuable because it makes Foclan much more useful in data and automation pipelines without changing the language core.

### 7. `foclan-http` evolution

`foclan-http` now exists in first form. The next steps are:

- deterministic HTTP PUT/PATCH/DELETE helpers where clearly useful
- clearer retry and timeout diagnostics
- better response error shaping
- safer convenience around auth headers and common JSON APIs

This should remain an extension, not core syntax.

### 8. `foclan-schemas`

Potential extension package:

- JSON Schema helpers
- schema templates
- schema validation for final outputs

This is a strong fit because exact output contracts are already central to Foclan.

### 9. `foclan-sql` evolution

`foclan-sql` now exists in first form. The next steps are:

- Postgres and other mainstream SQL backends where they fit the same narrow request model
- clearer connection presets
- transaction helpers only if they stay simple
- stronger documentation for SQL-first data pipelines

This fits the product direction very well because SQL is already declarative, data-oriented, and familiar to LLMs.

## Bridge Directions

### 10. Bridge runtimes

The strongest candidate for new core capability is not a large syntax expansion.

It is a small bridge mechanism that would let Foclan:

- keep its constrained LLM-friendly core
- and hand one narrow step to another runtime when that is cleaner

The most likely first bridge is:

- `foclan-python`

This would be valuable because it gives Foclan an escape hatch without forcing the core language to become general-purpose.

## Possible Core Improvements

These are only worth doing if they clearly improve LLM behavior.

### 11. Safer nested output helpers

The strongest candidate for core evolution is any syntax that reduces:

- wrong output shape
- duplicated helper structure
- nested key drift

But it should only be added if it is simpler than today's patterns, not just "more powerful."

### 12. Simpler project-level conventions

The language may not need more syntax if the product grows better conventions:

- fixed folder layout
- fixture conventions
- standard prompt bundles
- standard benchmark flow

That may provide more real value than new operators.

## Strong Reasons For Developers To Try Foclan

These are the product arguments worth sharpening over time:

- Foclan gives LLMs a smaller search space for exact data programs.
- It turns "LLM glue code" into a benchmarkable layer.
- It is easier to inspect than hidden chain-of-thought or tool-driven planning.
- It may outperform Python specifically in exact-output tasks, even when Python remains the main application language.
- It is small enough to learn quickly, but structured enough to be measured.

## What Not To Do

Avoid these unless there is overwhelming evidence:

- turning Foclan into a general-purpose language
- adding loops, classes, or large mutable-state features
- adding provider-specific syntax directly into the core language
- using bridges as an excuse to stop caring about a clean core
- optimizing for human cleverness instead of LLM reliability
