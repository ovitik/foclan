# foclan-sql

`foclan-sql` is the optional extension package for deterministic SQL query and exec steps.

The first public version is intentionally narrow:

- SQLite-first
- explicit request records
- list-of-record query results
- no ORM layer
- no SQL-specific core syntax

## Install

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-sql"
```

## Host Functions

- `sql_query`
- `sql_exec`

## Usage

Query rows:

```focus
in request
call sql_query
out
```

with:

```json
{
  "request": {
    "path": "data/app.db",
    "sql": "select city, count(*) as total from users group by city order by total desc"
  }
}
```

Execute a write:

```focus
in request
call sql_exec
out
```

with:

```json
{
  "request": {
    "path": "data/app.db",
    "sql": "insert into users(name, city) values (:name, :city)",
    "params": {
      "name": "Ada",
      "city": "Prague"
    }
  }
}
```

## Connection Inputs

Provide one of:

- `path`
- `dsn`
- `dsn_env`

Current `dsn` support is intentionally narrow:

- `sqlite:///:memory:`
- `sqlite:///relative/or/absolute/path.db`

If you use `dsn_env`, you can combine it with:

```bash
foclan run program.focus --env request.json --dotenv .env
```
