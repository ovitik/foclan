# Bridges

Bridges are a planned core capability for handing off one narrow step of a Foclan workflow to another runtime.

The idea is simple:

- keep Foclan small and LLM-optimized
- do not force the core language to express everything
- allow a controlled escape hatch when another language is clearly the better fit for one step

## Why Bridges Matter

Without bridges, the pressure on the core language keeps growing:

- more syntax
- more special cases
- more teaching burden
- more opportunities for LLM drift

With bridges, Foclan can stay focused on what it does best:

- linear orchestration
- exact output shaping
- deterministic data workflow

and hand off special cases elsewhere.

## Intended Role

Bridges are not meant to replace extensions.

They are meant for cases where:

- the step is highly custom
- the step is hard to express elegantly in Foclan
- the step is not worth turning into a reusable extension

Examples:

- custom regex-heavy parsing
- unusual scoring logic
- one-off transformations
- calculations that are clearer in another language

## Planned Model

The current direction is:

- Foclan core gets a small `bridge <runtime>` construct
- concrete bridge runtimes are installed through extension packages

That means the core would know how to:

- enter a bridge block
- pass the current `focus`
- receive a new `focus`

But the actual runtime would be provided by a package such as:

- `foclan-python`
- future `foclan-sql`
- perhaps later other runtimes if justified

## High-Level Semantics

The default bridge model should be:

- input: current `focus`
- execution: small block in another runtime
- output: `result`
- new `focus`: value of `result`

In other words:

- `focus` goes in
- `result` comes out
- then Foclan continues

## Design Constraints

Bridge support should only ship if it preserves the small-core philosophy.

The minimum requirements are:

- explicit runtime name
- explicit block boundary
- clear `focus -> result` contract
- JSON-compatible output
- timeout support
- strict sandboxing or execution policy for unsafe runtimes

## Safety Direction

The likely first bridge runtime is Python, but not as a full unrestricted shell.

The expected direction is:

- restricted builtins
- no implicit imports
- no implicit filesystem or network access
- timeout on execution
- explicit policy if unsafe execution is ever allowed

## Product Impact

Bridges change the role of Foclan in an important way.

Foclan no longer needs to be:

- fully general-purpose

It only needs to be:

- excellent at the constrained, LLM-friendly center of the workflow
- and excellent at handing off the exceptions in a controlled way

That is likely the strongest long-term direction for the language.

The concrete draft syntax, runtime contract, and plugin model are in [BRIDGE_SPEC.md](BRIDGE_SPEC.md).
