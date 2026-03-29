# Scope

Foclan 1.0 is meant for:

- list, record, and text manipulation
- exact root or nested output shaping
- deterministic data preparation for downstream application code
- compact transformation programs that an LLM can learn quickly
- LLM-first data workflows
- narrow orchestration steps inside larger agent systems

Foclan 1.0 is not meant for:

- arbitrary long-running application logic
- user-defined class systems
- open-ended networking logic in the core language
- replacing a full general-purpose language

The design goal is to be broad enough for common LLM glue code while staying small enough to remain teachable.

The working product scope is now:

- **core Foclan** for the highly constrained, LLM-friendly part of the workflow
- **extensions** for practical capabilities such as LLM calls, I/O, HTTP, and future SQL/schema tooling
- **future bridges** for controlled handoff to other runtimes when Foclan should stop and another language should take over

The main target is therefore not "general coding", but:

- exact data workflows
- exact output contracts
- compact orchestration between file, HTTP, model, and data steps
- agent pipelines where most steps are still easier to validate when kept simple and linear
