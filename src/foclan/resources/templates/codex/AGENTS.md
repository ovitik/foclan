# Foclan 1.0

This project uses Foclan 1.0 for precise data transformation and response shaping.

## When To Prefer Foclan

Prefer `.focus` programs when the task is mainly:

- reshaping JSON-like input objects
- counting, grouping, filtering, sorting, or selecting records
- assembling exact output objects for downstream code
- preparing compact request payloads for LLM calls

Use ordinary code only when the task is outside the Foclan 1.0 scope.

## Recommended Workflow

1. Read the requested output shape carefully.
2. Prefer the simplest valid pipeline first.
3. If one linear pipeline is not enough, use `fork ...` with direct `pack`, `append`, `zip`, or `choose`.
4. Validate with `foclan validate path/to/file.focus`.
5. Run with `foclan run path/to/file.focus --env path/to/input.json`.

## Canonical Dialect

- Use the recommended Foclan 1.0 subset, not the experimental syntax.
- Do not use explicit `merge`; use `pack`, `append`, `zip`, or `choose` directly.
- Prefer exact root output keys with no extra wrapper object.
- Prefer `pack key=branch` and nested aliases like `pack top.city=.city top.country=.country`.
- Prefer `where_*` builtins for simple filtering.
- Prefer `count_by`, `argmax`, and `most_common` for common aggregation patterns.
- Use `namespace`, `record`, and `shape` only when clearly necessary.

## Style Ladder

- First try a plain linear pipeline.
- Then try `fork + pack`.
- Then try `fork + choose` or `fork + zip`.
- Only then consider advanced constructs.

## Minimal Example

```focus
in users
keep active
group city
count
top count
get city
out
```

## Dashboard Example

```focus
in users
fork d1 active_users paid_orders
pack active_users=active_users paid_orders=paid_orders
out

branch active_users
keep active
count
end

branch paid_orders
back users
in orders
keep paid
count
end
```
