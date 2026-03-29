# Bridge Spec Draft

This document captures the intended first bridge design for Foclan.

It is a specification target, not a shipped feature.

## Goal

Add one small core construct that lets a Foclan program hand a narrow step to another runtime without turning Foclan itself into a general-purpose language.

The bridge mechanism should:

- preserve the linear `focus` model
- preserve exact output discipline
- add expressiveness only where needed
- keep bridge runtimes modular through extension packages

## Proposed Syntax

The current proposed syntax is:

```focus
in users
bridge python
result = [user["name"] for user in focus if user.get("active")]
end
out
```

Meaning:

- current `focus` is passed into the named bridge runtime
- the bridge block runs in that runtime
- the bridge block must assign `result`
- `result` becomes the new `focus`
- Foclan execution then continues normally

## Core Semantics

The default bridge contract is:

- input variable: `focus`
- output variable: `result`

This is intentionally minimal.

Bridge blocks should not:

- access Foclan branch names
- mutate Foclan flow state
- directly interact with `fork`, `branch`, or `out`

They are pure transformation steps embedded in a larger Foclan flow.

## Data Contract

Bridge runtimes must accept JSON-compatible Foclan values:

- null
- bool
- number
- string
- list
- record

Bridge runtimes must also return JSON-compatible values.

This keeps the handoff boundary explicit and makes validation easier.

## Parser Constraints

The parser should treat a bridge block as:

- a statement with a runtime name
- raw block text payload
- terminated by `end`

The core parser should not interpret the contents of the bridge block itself.

## Runtime Contract

The core runtime should resolve a bridge runtime from a registry and invoke it with:

- runtime block source
- current focus
- execution policy

In Python-like pseudocode:

```python
new_focus = bridge_runtime.handler(block_source, focus, policy)
```

The returned value becomes the next Foclan `focus`.

## Plugin Architecture

Bridge runtimes should be registered through a dedicated plugin group:

- `foclan.bridge_runtimes`

The public core package now includes a draft registry layer in:

- `foclan.bridges`

The expected first extension package is:

- `foclan-python`

Later candidates:

- `foclan-sql`
- other runtimes only if they clearly fit the product vision

## Execution Policy

The draft execution policy currently contains:

- `timeout_seconds`
- `allow_imports`
- `allow_filesystem`
- `allow_network`

The likely default should be very restrictive.

## Safety Rules

The first bridge runtime should be treated as a constrained transform runtime, not as a full scripting environment.

Recommended initial rules:

- timeout required
- no implicit imports
- no filesystem access
- no network access
- no ambient project state
- small builtins surface
- one input (`focus`), one output (`result`)

If a less restricted mode is ever added, it should be:

- explicit
- opt-in
- clearly labeled unsafe

## Product Rules

Bridges are justified when:

- a step is custom and not reusable enough for an extension
- expressing the step in core Foclan would add harmful syntax or complexity
- the bridge block is smaller and clearer than the equivalent host-function workaround

Bridges are not justified when:

- the need is common enough to deserve a reusable extension
- the bridge is used only because the author prefers another language
- the bridge would become the main body of the program rather than a narrow step

## Intended First Runtime

`foclan-python` should be the first implementation target.

Why:

- it is familiar to LLMs
- it covers many awkward edge cases
- it gives Foclan a practical escape hatch quickly

But it should still be constrained enough that Foclan remains the main orchestration language.
