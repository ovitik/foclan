# Few-Shot Examples

## Example 1: Top active city

What it does: keeps active users and returns the most common city.

```text
in users
keep active
most_common city
out
```

## Example 2: Flat root dashboard

What it does: returns `{active_users, paid_orders}` directly at root.

```text
fork d1 active_users paid_orders
pack active_users paid_orders
out

branch active_users
in users
keep active
count
end

branch paid_orders
in orders
keep paid
count
end
```

## Example 3: Exact nested output

What it does: returns `{top: {city, country}}` without extra wrappers.

```text
fork d1 top
pack top
out

branch top
fork d2 .city .country
pack city=.city country=.country
end

branch .city
in users
keep active
most_common city
end

branch .country
in orders
keep paid
most_common country
end
```

## Example 4: Choose stats vs meta

What it does: if `flag` is true, return counts; otherwise return lightweight metadata.

```text
in flag
fork d1 stats meta
choose stats meta
out

branch stats
fork d2 active_users paid_orders
pack active_users paid_orders
end

branch active_users
in users
keep active
count
end

branch paid_orders
in orders
keep paid
count
end

branch meta
fork d2 profile_keys first_names
pack profile_keys first_names
end

branch profile_keys
in profile
keys
sort
end

branch first_names
in users
keep active
map name
take 3
end
```

## Example 5: Root aliases

What it does: returns exact root keys even when the inner branch names are shorter.

```text
fork d1 user order
pack top_user=user top_order=order
out

branch user
in users
argmax score
end

branch order
in orders
argmax total
end
```

## Example 6: Request payload assembly

What it does: builds a simple provider payload object without making the API call itself.

```text
fork d1 provider model prompt
pack provider model prompt
out

branch provider
const "openai"
end

branch model
const "gpt-5.4"
end

branch prompt
in question
end
```

## Example 7: Live JSON extraction

What it does: builds one request object and sends it to `llm_json`.

```text
fork d1 provider model system input schema max_output_tokens
pack provider=provider model=model system=system input=input schema=schema max_output_tokens=max_output_tokens
call llm_json
out

branch provider
const "openai"
end

branch model
const "gpt-5-mini"
end

branch system
const "Extract a compact person record."
end

branch input
in raw_text
end

branch schema
in schema
end

branch max_output_tokens
const 200
end
```
