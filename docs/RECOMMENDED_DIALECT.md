# Recommended Dialect

This is the canonical Foclan 1.0 style.

## Style Ladder

Use the first style that solves the task:

1. plain linear pipeline
2. one root `fork` plus direct `pack`, `zip`, `append`, or `choose`
3. nested output via `pack top.city=.city`
4. only if collisions are unavoidable, use `namespace`
5. only if a wrapper key is truly required, use `record`
6. use `shape` only when exact nested-key drift is a real risk

## Default Subset

Prefer these by default:

- `in`, `out`
- `const`
- `fork`, `branch`, `end`
- `pack`, `append`, `zip`, `choose`
- `keep`, `drop`, `where_true`, `where_false`, `where_eq`, `where_gt`
- `map`, `group`, `count`, `count_by`, `top`, `sort`, `take`, `uniq`
- `keys`, `len`, `get`, `argmax`, `most_common`
- `call` when you intentionally use an installed host function such as `llm_text` or `llm_json`

Treat these as advanced:

- `namespace`
- `record`
- `shape`
- `back`

## Output Rules

- return exactly the requested shape
- do not add wrapper objects unless requested
- prefer `pack key=branch`
- prefer `pack top.city=.city top.country=.country` for nested output
- prefer keeping large schemas and request constants in input JSON unless the value is tiny

## Example

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
in orders
keep paid
count
end
```
