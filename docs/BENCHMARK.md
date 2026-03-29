# Public Benchmark Plan

Foclan should ship with a public benchmark that users can run themselves.

## Goals

- keep the benchmark reproducible
- keep the task bundle stable
- let the user choose provider and model
- compare Foclan against a stable baseline language
- measure correctness first, then token cost and latency

## Recommended Baseline

Use Python as the default fixed comparison language.

Why:

- it is the most recognizable baseline
- it avoids benchmark fragmentation across many arbitrary languages
- it lets users answer the practical question: "is Foclan better than Python for this model?"

The public runner can still allow `--language foclan` for single-language runs, but the canonical comparison should be:

- `foclan`
- `python`

## Task Bundle

The public repository already includes a bundled exact-output suite:

- `benchmarks/main-106.json`

It contains `106` tasks across five difficulties:

- `easy`
- `medium`
- `hard`
- `brutal`
- `super_brutal`

Each task includes:

- `task_id`
- `title`
- `description`
- `difficulty`
- `env`
- `expected`

This makes it possible to evaluate generated solutions without shipping the private benchmark harness.

## Public Runner Requirements

The public benchmark runner should support:

- provider selection:
  - `openai`
  - `anthropic`
  - `google`
- user-selected model name
- language selection:
  - default `foclan python`
  - optional single-language runs
- difficulty filters
- task-count limit or random sample
- output directory for machine-readable reports

## Metrics

The runner should report:

- correctness
- visible code size
- billed output tokens
- reasoning tokens when the provider exposes them
- cached input tokens when the provider exposes them
- end-to-end latency

Correctness should remain the primary metric.

## Why This Matters

This public benchmark should answer a simple practical question:

> For a chosen model, is Foclan a better language than Python for exact, difficult LLM-generated data programs?

## Current Status

This repository now contains the public task bundle and benchmark spec.

The next implementation step is the public runner itself.
