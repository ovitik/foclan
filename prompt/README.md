# Prompt Bundle

Recommended production prompt assembly order:

1. [system_guide.md](system_guide.md)
2. [few_shot_examples.md](few_shot_examples.md)
3. [task_template.md](task_template.md)
4. Optional: [anti_overthinking.md](anti_overthinking.md)

The default product stance should be:

- keep the guide stable
- keep the examples short and representative
- treat anti-overthinking as a controllable addendum, not a new language

The same prompt bundle is also packaged into the installable CLI and can be rendered with:

```bash
foclan prompt
foclan prompt --anti-overthinking
```
