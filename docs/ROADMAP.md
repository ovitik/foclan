# Roadmap

The first public milestone is simple:

- publish a clean installable package
- keep one stable recommended dialect
- ship prompt bundle, examples, and editor scaffolds
- prove the install path works in Codex and Cursor

After that, the priority should be:

- improve exact-output reliability further
- reduce prompt teaching cost and reasoning overhead
- keep the core language small while expanding capability through extensions
- make Foclan more useful in real AI application workflows without turning it into a general-purpose language
- define a clean bridge mechanism so Foclan can hand off narrow steps to other runtimes without bloating the core

The main product question is no longer "can Foclan exist?"

It is:

> can Foclan become the best narrow language for LLM-written exact data programs?

The roadmap should therefore stay disciplined:

1. strengthen the core dialect
2. add practical product workflow features
3. add extensions before adding core syntax
4. add bridge support only if it preserves the small-core philosophy
5. only add core language features when they clearly improve:
   - correctness
   - token efficiency
   - latency
   - teachability

Near-term extension direction:

- keep strengthening `foclan-llm`, `foclan-io`, and `foclan-http`
- add future high-value extensions such as SQL and schema tooling
- use bridge runtimes for expressiveness instead of expanding core syntax too aggressively
