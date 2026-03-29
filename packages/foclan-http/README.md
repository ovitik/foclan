# foclan-http

`foclan-http` is the optional extension package for simple deterministic HTTP calls.

It adds:

- `http_get_json`
- `http_get_text`
- `http_post_json`

## Install

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-http"
```

## Header values from `.env`

Headers may be plain strings:

```json
{
  "Authorization": "Bearer abc"
}
```

or environment-backed objects:

```json
{
  "Authorization": {"env": "MY_API_KEY", "prefix": "Bearer "}
}
```

Use with:

```bash
foclan run program.focus --env request.json --dotenv .env
```

`request.json` should contain the named program input, for example:

```json
{
  "request": {
    "url": "https://api.example.com/items",
    "headers": {
      "Authorization": {"env": "MY_API_KEY", "prefix": "Bearer "}
    }
  }
}
```
