# foclan-io

`foclan-io` is the optional extension package for local file and tabular I/O.

It adds:

- `read_text`
- `write_text`
- `read_json`
- `write_json`
- `read_jsonl`
- `read_csv`
- `write_csv`

## Install

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-io"
```

## Usage

Read JSON:

```focus
in request
call read_json
out
```

with:

```json
{
  "request": {
    "path": "inputs/data.json"
  }
}
```

Write JSON:

```focus
in request
call write_json
out
```

with:

```json
{
  "request": {
    "path": "outputs/result.json",
    "content": {
      "ok": true
    }
  }
}
```
