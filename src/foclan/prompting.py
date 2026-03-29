from __future__ import annotations

from dataclasses import dataclass

from .resources import read_text


@dataclass(frozen=True)
class PromptBundle:
    system_guide: str
    few_shot_examples: str
    task_template: str
    anti_overthinking: str

    def assemble(
        self,
        include_anti_overthinking: bool = False,
        task_text: str | None = None,
        inputs_json: str | None = None,
    ) -> str:
        parts = [
            self.system_guide.strip(),
            self.few_shot_examples.strip(),
        ]
        if include_anti_overthinking:
            parts.append(self.anti_overthinking.strip())

        task_block = self.task_template.strip()
        if task_text is not None:
            task_block = task_block.replace("`<describe the desired output precisely>`", task_text)
        if inputs_json is not None:
            task_block = task_block.replace("<insert the named input schema or representative input object>", inputs_json)
        parts.append(task_block)
        return "\n\n".join(part for part in parts if part)


def load_prompt_bundle() -> PromptBundle:
    return PromptBundle(
        system_guide=read_text("prompt", "system_guide.md"),
        few_shot_examples=read_text("prompt", "few_shot_examples.md"),
        task_template=read_text("prompt", "task_template.md"),
        anti_overthinking=read_text("prompt", "anti_overthinking.md"),
    )
