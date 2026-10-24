from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import scripts.finish_milestone as finisher
from scripts.finish_milestone import Report, finish


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _write_plan(
    repo: Path,
    allowed: list[str],
    *,
    forbidden: list[str] | None = None,
) -> Path:
    plan = repo / "plan.md"
    allowed_lines = "\n".join(f"- {path}" for path in allowed)
    forbidden_lines = "\n".join(
        f"- {path}" for path in (forbidden or ["data/**", "models/**"])
    )
    plan.write_text(
        "# Plan\n\n"
        "## Version-control allowlist\n\n"
        "Tracked files or directories allowed:\n\n"
        f"{allowed_lines}\n\n"
        "Generated artifacts forbidden:\n\n"
        f"{forbidden_lines}\n\n"
        "Expected commit message:\n\n"
        "- feat(test): finish safely\n\n"
        "## Results\n",
        encoding="utf-8",
    )
    return plan


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repository"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "--", "README.md")
    _git(repo, "commit", "-qm", "initial")
    return repo


def _finish(repo: Path, plan: Path, mode: str, *, message: str | None = None) -> Report:
    return finish(repo, plan, mode, message=message, validators=())


def test_default_validators_use_current_interpreter() -> None:
    commands = finisher._default_validators()

    python_commands = [command for command in commands if command[0] != "git"]
    assert python_commands
    assert all(command[0] == sys.executable for command in python_commands)
    assert all(command[1] == "-m" for command in python_commands)
    assert "/usr/bin/python3" not in Path(finisher.__file__).read_text(encoding="utf-8")


def test_missing_validation_tool_reports_interpreter(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _write_plan(git_repo, ["plan.md"])
    real_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: None if name == "ruff" else real_find_spec(name),
    )

    report = finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error == (
        f"validation tool(s) unavailable in interpreter {sys.executable!r}: ruff"
    )


def test_stage_preserves_index_when_validation_fails(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "README.md"])
    _git(git_repo, "add", "--", "plan.md")
    (git_repo / "README.md").write_text("changed\n", encoding="utf-8")
    before_tree = _git(git_repo, "write-tree")

    report = finish(
        git_repo,
        plan,
        "stage",
        validators=((sys.executable, "-c", "raise SystemExit(7)"),),
    )

    assert not report.ok
    assert report.error is not None
    assert "validation failed" in report.error
    assert _git(git_repo, "write-tree") == before_tree


def test_commit_is_blocked_when_validation_fails(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md"])
    _git(git_repo, "add", "--", "plan.md")
    before = _git(git_repo, "rev-parse", "HEAD").strip()

    report = finish(
        git_repo,
        plan,
        "commit",
        message="feat(test): finish safely",
        validators=((sys.executable, "-c", "raise SystemExit(8)"),),
    )

    assert not report.ok
    assert report.error is not None
    assert "validation failed" in report.error
    assert _git(git_repo, "rev-parse", "HEAD").strip() == before


def test_check_detects_file_outside_allowlist(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "allowed.py"])
    (git_repo / "allowed.py").write_text("VALUE = 1\n", encoding="utf-8")
    (git_repo / "unexpected.txt").write_text("outside\n", encoding="utf-8")

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.out_of_scope == ["unexpected.txt"]


def test_check_reports_allowed_untracked_file(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "different_name.py"])
    (git_repo / "different_name.py").write_text("VALUE = 1\n", encoding="utf-8")

    report = _finish(git_repo, plan, "check")

    assert report.ok
    assert report.untracked == ["different_name.py", "plan.md"]
    assert report.in_scope == ["different_name.py", "plan.md"]


@pytest.mark.parametrize("forbidden_path", ["data/raw.csv", ".env"])
def test_check_rejects_always_forbidden_paths(
    git_repo: Path, forbidden_path: str
) -> None:
    target = git_repo / forbidden_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("do not stage\n", encoding="utf-8")
    plan = _write_plan(git_repo, ["plan.md", forbidden_path])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error is not None
    assert "forbidden path" in report.error


def test_check_rejects_symlink(git_repo: Path) -> None:
    (git_repo / "target.txt").write_text("target\n", encoding="utf-8")
    (git_repo / "linked.txt").symlink_to("target.txt")
    plan = _write_plan(git_repo, ["plan.md", "linked.txt", "target.txt"])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error is not None
    assert "symlink" in report.error


def test_check_rejects_path_traversal(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "../outside.txt"])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error is not None
    assert "unsafe or ambiguous" in report.error


def test_stage_adds_only_literal_allowlisted_paths_with_spaces(git_repo: Path) -> None:
    directory = git_repo / "folder with spaces"
    directory.mkdir()
    allowed = directory / "new name.py"
    allowed.write_text("VALUE = 1\n", encoding="utf-8")
    plan = _write_plan(git_repo, ["plan.md", "folder with spaces/new name.py"])

    report = _finish(git_repo, plan, "stage")

    assert report.ok
    assert report.staged == ["folder with spaces/new name.py", "plan.md"]
    recorded_commands = [entry["command"] for entry in report.commands]
    assert all(isinstance(command, list) for command in recorded_commands)
    add_commands = [
        command
        for command in recorded_commands
        if isinstance(command, list) and command[:2] == ["git", "add"]
    ]
    expected_add = [
        "git",
        "add",
        "--",
        "folder with spaces/new name.py",
        "plan.md",
    ]
    assert add_commands == [expected_add, expected_add]
    assert all(command != ["git", "add", "."] for command in add_commands)


def test_commit_requires_message_and_does_not_commit(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "README.md"])
    _git(git_repo, "add", "--", "plan.md")
    before = _git(git_repo, "rev-parse", "HEAD").strip()

    report = _finish(git_repo, plan, "commit")

    assert not report.ok
    assert report.error == "--commit requires an explicit --message"
    assert _git(git_repo, "rev-parse", "HEAD").strip() == before


def test_commit_blocks_staged_path_outside_allowlist(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md"])
    (git_repo / "outside.txt").write_text("outside\n", encoding="utf-8")
    _git(git_repo, "add", "--", "plan.md", "outside.txt")

    report = _finish(
        git_repo,
        plan,
        "commit",
        message="feat(test): finish safely",
    )

    assert not report.ok
    assert report.error is not None
    assert "outside" in report.error


def test_commit_creates_commit_only_with_exact_explicit_message(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md"])
    _git(git_repo, "add", "--", "plan.md")
    before = _git(git_repo, "rev-parse", "HEAD").strip()

    report = _finish(
        git_repo,
        plan,
        "commit",
        message="feat(test): finish safely",
    )

    assert report.ok
    assert report.commit_created is not None
    assert report.commit_created != before
    assert _git(git_repo, "log", "-1", "--pretty=%s").strip() == (
        "feat(test): finish safely"
    )


def test_commit_rejects_message_different_from_plan(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md"])
    _git(git_repo, "add", "--", "plan.md")
    before = _git(git_repo, "rev-parse", "HEAD").strip()

    report = _finish(git_repo, plan, "commit", message="feat(test): other")

    assert not report.ok
    assert report.error == "commit message does not match the ExecPlan"
    assert _git(git_repo, "rev-parse", "HEAD").strip() == before


def test_check_does_not_alter_worktree_or_index(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "README.md"])
    (git_repo / "README.md").write_text("changed\n", encoding="utf-8")
    before_status = _git(
        git_repo, "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    before_index = _git(git_repo, "write-tree")

    report = _finish(git_repo, plan, "check")

    after_status = _git(
        git_repo, "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    after_index = _git(git_repo, "write-tree")
    assert report.ok
    assert after_status == before_status
    assert after_index == before_index


def test_stage_blocks_existing_staged_path_outside_allowlist(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "README.md"])
    (git_repo / "README.md").write_text("changed\n", encoding="utf-8")
    (git_repo / "outside.txt").write_text("outside\n", encoding="utf-8")
    _git(git_repo, "add", "--", "outside.txt")

    report = _finish(git_repo, plan, "stage")

    assert not report.ok
    assert report.error is not None
    assert "outside" in report.error
    assert _git(git_repo, "diff", "--cached", "--name-only").splitlines() == [
        "outside.txt"
    ]


def test_check_rejects_nonexistent_allowlist_path(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "missing.py"])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error == "allowlist path does not exist: missing.py"


def test_file_allowlist_entry_does_not_authorize_descendants(git_repo: Path) -> None:
    directory = git_repo / "docs" / "example.md"
    directory.mkdir(parents=True)
    (directory / "payload.py").write_text("VALUE = 1\n", encoding="utf-8")
    plan = _write_plan(git_repo, ["plan.md", "docs/example.md"])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.out_of_scope == ["docs/example.md/payload.py"]


@pytest.mark.parametrize(
    ("path", "content"),
    [
        ("release/model.bin", b"binary model"),
        ("release/model.pt", b"binary model"),
        ("release/model.keras", b"binary model"),
        ("release/lightgbm-model.txt", b"tree\n"),
        ("settings.yaml", b"api" + b"_key: " + b"sk-" + b"proj-example-value\n"),
        ("credentials.toml", b"pass" + b"word = example-value\n"),
    ],
)
def test_check_rejects_more_model_and_secret_artifacts(
    git_repo: Path, path: str, content: bytes
) -> None:
    target = git_repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    plan = _write_plan(git_repo, ["plan.md", path])

    report = _finish(git_repo, plan, "check")

    assert not report.ok
    assert report.error is not None
    assert "forbidden path" in report.error or "probable secret" in report.error


def test_failed_stage_preflight_preserves_real_index(git_repo: Path) -> None:
    plan = _write_plan(git_repo, ["plan.md", "bad.py"])
    (git_repo / "bad.py").write_text("VALUE = 1   \n", encoding="utf-8")
    before_tree = _git(git_repo, "write-tree")

    report = _finish(git_repo, plan, "stage")

    assert not report.ok
    assert _git(git_repo, "write-tree") == before_tree
    assert _git(git_repo, "diff", "--cached", "--name-only") == ""
