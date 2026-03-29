# foclan-python

`foclan-python` is the optional bridge runtime package for handing one narrow Foclan step to constrained Python.

It is intended for cases where:

- the workflow should stay mostly in Foclan
- one transform step is awkward to express in pure Foclan
- turning that step into a whole new core feature would be a mistake

## Install

```bash
python -m pip install "git+https://github.com/ovitik/foclan.git"
python -m pip install "git+https://github.com/ovitik/foclan.git#subdirectory=packages/foclan-python"
```

## Planned Foclan Usage

```focus
in users
bridge python
result = [user["name"] for user in focus if user.get("active")]
end
out
```

The bridge contract is:

- `focus` is the input
- bridge code must assign `result`
- `result` becomes the new Foclan focus

## Safety Direction

The runtime is intentionally constrained:

- no imports by default
- no filesystem access by default
- no network access by default
- timeout-limited execution

This is meant to be a narrow transform runtime, not a general unrestricted Python shell.
