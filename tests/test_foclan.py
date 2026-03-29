from pathlib import Path

import pytest

import foclan.benchmarking as foclan_benchmarking
import foclan.cli as foclan_cli
import foclan.extensions as foclan_extensions
from foclan import load_prompt_bundle, load_public_tasks, parse_program, run_benchmark, run_program_text, validate_program
from foclan.cli import main as foclan_main
from foclan.examples import list_current_examples, load_example_env, load_example_source
from foclan.extensions import HostExtension
from foclan.scaffolding import write_scaffold


ROOT = Path(__file__).resolve().parents[1]


def test_current_examples_validate() -> None:
    examples = sorted((ROOT / "examples" / "current").glob("*.focus"))
    assert examples
    for path in examples:
        program = parse_program(path.read_text(encoding="utf-8"))
        validate_program(program)


def test_counts_dashboard_runs() -> None:
    source = (ROOT / "examples" / "current" / "counts_dashboard.focus").read_text(encoding="utf-8")
    env_path = ROOT / "examples" / "current" / "env" / "users_orders.json"
    env = __import__("json").loads(env_path.read_text(encoding="utf-8"))
    result = run_program_text(source, env=env)
    assert result.value == {"active_users": 3, "paid_orders": 3}


def test_top_city_program_runs() -> None:
    source = (ROOT / "examples" / "current" / "active_top_city.focus").read_text(encoding="utf-8")
    env_path = ROOT / "examples" / "current" / "env" / "users_orders.json"
    env = __import__("json").loads(env_path.read_text(encoding="utf-8"))
    result = run_program_text(source, env=env)
    assert result.value == "Prague"


def test_rejects_explicit_merge_keyword() -> None:
    source = """
in users
fork d1 a b
merge pack a b
out

branch a
count
end

branch b
count
end
""".strip()
    with pytest.raises(ValueError, match="does not allow explicit 'merge'"):
        parse_program(source)


def test_prompt_bundle_loads_and_assembles() -> None:
    bundle = load_prompt_bundle()
    prompt = bundle.assemble(
        include_anti_overthinking=True,
        task_text="return the top active city",
        inputs_json='{"users": []}',
    )
    assert "Foclan 1.0" in bundle.system_guide
    assert "Anti-Overthinking Addendum" in bundle.anti_overthinking
    assert "return the top active city" in prompt
    assert '{"users": []}' in prompt


def test_current_examples_are_packaged() -> None:
    entries = list_current_examples()
    assert entries
    for entry in entries:
        assert load_example_source(entry)
        assert load_example_env(entry)


def test_cli_examples_list_outputs_current_examples(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = foclan_main(["examples", "list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "counts_dashboard" in captured
    assert "prepare_llm_payload" in captured
    assert "openai_json_extract" in captured
    assert "requires_extensions" in captured


def test_cli_examples_run_counts_dashboard(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = foclan_main(["examples", "run", "counts_dashboard"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert '"active_users": 3' in captured
    assert '"paid_orders": 3' in captured


def test_cli_examples_run_accepts_dotenv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPENAI_API_KEY=test\n", encoding="utf-8")
    loaded: list[Path] = []
    monkeypatch.setattr(foclan_cli, "_load_dotenv", lambda path: loaded.append(path))
    exit_code = foclan_main(["examples", "run", "counts_dashboard", "--dotenv", str(dotenv_path)])
    capsys.readouterr()
    assert exit_code == 0
    assert loaded == [dotenv_path]


def test_cli_examples_run_llm_example_requires_extension(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(foclan_cli, "list_installed_extensions", lambda: ())
    with pytest.raises(RuntimeError, match="requires missing extension"):
        foclan_main(["examples", "run", "openai_json_extract"])


def test_write_scaffold_creates_codex_and_cursor_files(tmp_path: Path) -> None:
    written = write_scaffold("all", tmp_path)
    assert tmp_path.joinpath("AGENTS.md") in written
    assert tmp_path.joinpath(".cursor", "rules", "foclan-v1.mdc") in written
    assert "Foclan 1.0" in tmp_path.joinpath("AGENTS.md").read_text(encoding="utf-8")


def test_cli_init_cursor_writes_rule(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = foclan_main(["init", "cursor", "--project-dir", str(tmp_path)])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "foclan-v1.mdc" in captured
    assert tmp_path.joinpath(".cursor", "rules", "foclan-v1.mdc").exists()


def test_cli_init_project_writes_starter_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = foclan_main(["init", "project", "--project-dir", str(tmp_path)])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "counts_dashboard.focus" in captured
    assert tmp_path.joinpath("README.md").exists()
    assert tmp_path.joinpath("programs", "counts_dashboard.focus").exists()
    assert tmp_path.joinpath("programs", "extract_contact.focus").exists()
    assert tmp_path.joinpath("inputs", "users_orders.json").exists()
    assert tmp_path.joinpath(".env.example").exists()
    assert tmp_path.joinpath("AGENTS.md").exists()
    assert tmp_path.joinpath(".cursor", "rules", "foclan-v1.mdc").exists()


def test_packaged_prompt_and_examples_match_repo_files() -> None:
    prompt_files = [
        "system_guide.md",
        "few_shot_examples.md",
        "task_template.md",
        "anti_overthinking.md",
    ]
    for name in prompt_files:
        repo_text = (ROOT / "prompt" / name).read_text(encoding="utf-8")
        packaged_text = (ROOT / "src" / "foclan" / "resources" / "prompt" / name).read_text(encoding="utf-8")
        assert packaged_text == repo_text

    example_files = sorted((ROOT / "examples" / "current").glob("*.focus"))
    for path in example_files:
        packaged = ROOT / "src" / "foclan" / "resources" / "examples" / "current" / path.name
        assert packaged.read_text(encoding="utf-8") == path.read_text(encoding="utf-8")

    template_files = [
        ROOT / "templates" / "project" / "README.md",
        ROOT / "templates" / "project" / "gitignore.txt",
        ROOT / "templates" / "project" / "env.example",
        ROOT / "templates" / "project" / "programs" / "counts_dashboard.focus",
        ROOT / "templates" / "project" / "programs" / "extract_contact.focus",
        ROOT / "templates" / "project" / "inputs" / "users_orders.json",
        ROOT / "templates" / "project" / "inputs" / "contact_extract.json",
    ]
    for path in template_files:
        packaged = ROOT / "src" / "foclan" / "resources" / "templates" / Path(*path.relative_to(ROOT / "templates").parts)
        assert packaged.read_text(encoding="utf-8") == path.read_text(encoding="utf-8")


def test_cli_accepts_utf8_bom_program_and_env(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    program = tmp_path / "counts_dashboard.focus"
    env_file = tmp_path / "users_orders.json"
    program.write_text(
        (
            "in users\n"
            "fork d1 active_users paid_orders\n"
            "pack active_users=active_users paid_orders=paid_orders\n"
            "out\n\n"
            "branch active_users\n"
            "keep active\n"
            "count\n"
            "end\n\n"
            "branch paid_orders\n"
            "in orders\n"
            "keep paid\n"
            "count\n"
            "end\n"
        ),
        encoding="utf-8-sig",
    )
    env_file.write_text(
        (
            '{\n'
            '  "users": [{"active": true}, {"active": false}, {"active": true}],\n'
            '  "orders": [{"paid": true}, {"paid": true}]\n'
            '}\n'
        ),
        encoding="utf-8-sig",
    )

    exit_code = foclan_main(["run", str(program), "--env", str(env_file)])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert '"active_users": 2' in captured


def test_call_is_allowed_in_product_subset() -> None:
    source = """
in request
call llm_text
out
""".strip()
    program = parse_program(source)
    validate_program(program)


def test_extensions_list_outputs_discovered_extensions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    extension = HostExtension(
        name="foclan-llm",
        description="LLM provider calls",
        host_functions={"llm_text": lambda focus: focus},
    )
    monkeypatch.setattr(foclan_extensions, "list_installed_extensions", lambda: (extension,))
    monkeypatch.setattr(foclan_cli, "list_installed_extensions", lambda: (extension,))
    exit_code = foclan_main(["extensions", "list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "foclan-llm" in captured
    assert "llm_text" in captured


def test_public_benchmark_suite_loads() -> None:
    tasks = load_public_tasks()
    assert len(tasks) == 106
    assert {task.difficulty for task in tasks} == {"easy", "medium", "hard", "brutal", "super_brutal"}


def test_cli_benchmark_list_suites(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = foclan_main(["benchmark", "list-suites"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "main-106" in captured


def test_run_benchmark_with_mock_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        foclan_benchmarking,
        "load_public_tasks",
        lambda **kwargs: [
            foclan_benchmarking.PublicEvalTask(
                task_id="active-users-count",
                title="Active Users Count",
                description="Return the number of active users.",
                difficulty="easy",
                env={"users": [{"active": True}, {"active": False}, {"active": True}]},
                expected=2,
            )
        ],
    )

    def fake_generate_code(**kwargs):
        language = "python" if "Python" in kwargs["system_prompt"] else "foclan"
        if language == "python":
            text = "def solve(inputs):\n    return sum(1 for user in inputs['users'] if user.get('active'))\n"
        else:
            text = "in users\nkeep active\ncount\nout\n"
        return foclan_benchmarking.GeneratedResponse(
            text=text,
            usage=foclan_benchmarking.ProviderUsage(
                input_tokens=10,
                cached_tokens=0,
                output_tokens=20,
                reasoning_tokens=0,
                total_tokens=30,
                resolved_model="mock-model",
            ),
        )

    monkeypatch.setattr(foclan_benchmarking, "_generate_code", fake_generate_code)
    report = run_benchmark(
        provider="openai",
        model="mock-model",
        languages=("foclan", "python"),
        suite="main-106",
        difficulties=("easy",),
        sample_size=None,
        seed=1,
        max_output_tokens=200,
        reasoning_effort="none",
        include_anti_overthinking=False,
        parallelism=1,
        timeout_seconds=1.0,
        output_dir=tmp_path,
    )
    assert len(report["overall_summary"]) == 2
    assert tmp_path.exists()
    assert Path(report["json_path"]).exists()
    assert Path(report["markdown_path"]).exists()
