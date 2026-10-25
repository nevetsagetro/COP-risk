#!/usr/bin/env python3
"""Inspect, validate, stage, and explicitly commit one milestone safely."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath

_REQUIRED_VALIDATION_TOOLS = ("ruff", "mypy", "pytest")

_SECTION = "## Version-control allowlist"
_ALLOWED = "Tracked files or directories allowed:"
_FORBIDDEN = "Generated artifacts forbidden:"
_MESSAGE = "Expected commit message:"
_GLOB_CHARS = frozenset("*?[]{}")
_SERIALIZED_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".h5",
    ".joblib",
    ".keras",
    ".onnx",
    ".parquet",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
}
_SECRET_RE = re.compile(
    rb"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|"
    rb"gh[pousr]_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{16,}|"
    rb"(?:api[_-]?key|secret|token|password|passwd|pwd)\s*[:=]\s*"
    rb"['\"]?[^\s'\"]{12,})",
    re.IGNORECASE,
)


class FinisherError(RuntimeError):
    """A safe-finishing invariant was not met."""


def _default_validators() -> tuple[tuple[str, ...], ...]:
    """Build validation commands from the interpreter running this process."""
    return (
        (sys.executable, "-m", "ruff", "format", "--check", "."),
        (sys.executable, "-m", "ruff", "check", "."),
        (sys.executable, "-m", "mypy", "src", "tests", "scripts"),
        (sys.executable, "-m", "pytest"),
        ("git", "diff", "--check"),
    )


def _validate_tool_availability() -> None:
    missing = [
        tool
        for tool in _REQUIRED_VALIDATION_TOOLS
        if importlib.util.find_spec(tool) is None
    ]
    if missing:
        joined = ", ".join(missing)
        interpreter = repr(sys.executable)
        raise FinisherError(
            f"validation tool(s) unavailable in interpreter {interpreter}: {joined}"
        )


@dataclass(frozen=True)
class Allowlist:
    allowed: tuple[str, ...]
    forbidden: tuple[str, ...]
    expected_message: str


@dataclass
class Report:
    mode: str
    plan: str
    initial_commit: str = ""
    modified_tracked: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    ignored_relevant: list[str] = field(default_factory=list)
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    commands: list[dict[str, object]] = field(default_factory=list)
    validations: list[dict[str, object]] = field(default_factory=list)
    staged: list[str] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    staged_diff: list[str] = field(default_factory=list)
    commit_created: str | None = None
    final_status: list[str] = field(default_factory=list)
    ok: bool = False
    error: str | None = None


def _run(
    repo: Path,
    command: Sequence[str],
    report: Report,
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    report.commands.append(
        {"command": list(command), "returncode": completed.returncode}
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise FinisherError(f"command failed ({completed.returncode}): {detail}")
    return completed


def _safe_literal_path(value: str, *, preserve_directory: bool = False) -> str:
    candidate = value.strip().replace("\\", "/")
    declared_directory = candidate.endswith("/")
    path = PurePosixPath(candidate)
    if (
        not candidate
        or candidate in {".", ".."}
        or path.is_absolute()
        or ".." in path.parts
        or any(character in candidate for character in _GLOB_CHARS)
        or candidate.startswith(("-", ":"))
        or any(ord(character) < 32 for character in candidate)
        or path.parts[0] == ".git"
    ):
        raise FinisherError(f"unsafe or ambiguous allowlist path: {value!r}")
    normalized = path.as_posix().rstrip("/")
    if not normalized:
        raise FinisherError(f"unsafe allowlist path: {value!r}")
    return f"{normalized}/" if preserve_directory and declared_directory else normalized


def parse_allowlist(plan: Path) -> Allowlist:
    """Parse the one exact, mandatory allowlist section from an ExecPlan."""
    try:
        lines = plan.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FinisherError(f"cannot read ExecPlan: {exc}") from exc
    starts = [index for index, line in enumerate(lines) if line.strip() == _SECTION]
    if len(starts) != 1:
        raise FinisherError(f"ExecPlan must contain exactly one {_SECTION!r} section")
    section: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if line.startswith("## "):
            break
        section.append(line.rstrip())

    groups: dict[str, list[str]] = {_ALLOWED: [], _FORBIDDEN: [], _MESSAGE: []}
    current: str | None = None
    seen: set[str] = set()
    for raw_line in section:
        line = raw_line.strip()
        if not line:
            continue
        if line in groups:
            if line in seen:
                raise FinisherError(f"duplicate allowlist label: {line}")
            seen.add(line)
            current = line
            continue
        if not line.startswith("- ") or current is None:
            raise FinisherError(f"unexpected content in allowlist section: {line!r}")
        groups[current].append(line[2:].strip())

    if seen != set(groups) or not all(groups.values()):
        raise FinisherError("allowlist section has missing or empty required groups")
    if len(groups[_MESSAGE]) != 1 or not groups[_MESSAGE][0]:
        raise FinisherError("ExecPlan must declare exactly one expected commit message")

    allowed = tuple(
        _safe_literal_path(item, preserve_directory=True) for item in groups[_ALLOWED]
    )
    if len(set(allowed)) != len(allowed):
        raise FinisherError("duplicate paths in allowlist")
    return Allowlist(allowed, tuple(groups[_FORBIDDEN]), groups[_MESSAGE][0])


def _is_allowed(path: str, entries: Sequence[str]) -> bool:
    return any(
        path.startswith(entry) if entry.endswith("/") else path == entry
        for entry in entries
    )


def _is_documentation_or_config(path: str) -> bool:
    return path.startswith(("docs/", "configs/")) or path.endswith(
        (".md", ".toml", ".yaml", ".yml", ".json")
    )


def _hard_forbidden_reason(path: str) -> str | None:
    pure = PurePosixPath(path.lower())
    parts = pure.parts
    name = pure.name
    if parts and parts[0] == "data":
        return "data path"
    if name == ".env" or name.startswith(".env.") and name != ".env.example":
        return "environment secret file"
    if any(
        part
        in {
            ".venv",
            "venv",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
        }
        for part in parts
    ):
        return "cache or virtual environment"
    if pure.suffix in _SERIALIZED_SUFFIXES:
        return "data or serialized model artifact"
    if any(token in name for token in ("credential", "private_key", "id_rsa")):
        return "credential file"
    if any(token in name for token in ("model", "booster", "weights")) and not (
        path.startswith(("docs/", "configs/"))
        or pure.suffix in {".md", ".rst", ".toml", ".yaml", ".yml", ".json"}
    ):
        return "probable serialized model artifact"
    if parts and parts[0] in {
        "artifacts",
        "mlruns",
        ".mlruns",
        "models",
        "predictions",
        "runs",
    }:
        return "generated model or run artifact"
    if len(parts) >= 2 and parts[:2] == ("reports", "local"):
        return "local generated report"
    if "prediction" in name:
        return "prediction artifact"
    if name.startswith("manifest") and "local" in parts:
        return "local generated manifest"
    return None


def _forbidden_reason(path: str, allowlist: Allowlist) -> str | None:
    hard = _hard_forbidden_reason(path)
    if hard is not None:
        return hard
    for pattern in allowlist.forbidden:
        normalized = pattern.replace("\\", "/").lstrip("./")
        if fnmatch.fnmatchcase(path, normalized) or (
            normalized.endswith("/**")
            and path.startswith(normalized[:-3].rstrip("/") + "/")
        ):
            if _is_documentation_or_config(path) and _is_allowed(
                path, allowlist.allowed
            ):
                return None
            return f"ExecPlan forbidden pattern {pattern!r}"
    return None


def _status(repo: Path, report: Report) -> tuple[list[str], list[str], list[str]]:
    raw = _run(
        repo,
        (
            "git",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
        ),
        report,
    ).stdout
    tracked: list[str] = []
    untracked: list[str] = []
    ignored: list[str] = []
    records = raw.split("\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4:
            raise FinisherError("unexpected Git status record")
        code, path = record[:2], record[3:].replace("\\", "/")
        if "R" in code or "C" in code:
            if index >= len(records) or not records[index]:
                raise FinisherError("incomplete Git rename status")
            source = records[index].replace("\\", "/")
            index += 1
            tracked.extend((source, path))
        elif code == "??":
            untracked.append(path)
        elif code == "!!":
            ignored.append(path)
        else:
            tracked.append(path)
    return sorted(set(tracked)), sorted(set(untracked)), sorted(set(ignored))


def _assert_repo(repo: Path, plan: Path) -> tuple[Path, Path]:
    root_result = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if root_result.returncode != 0:
        raise FinisherError("target is not a Git repository")
    root = Path(root_result.stdout.strip()).resolve()
    candidate = plan if plan.is_absolute() else root / plan
    resolved_plan = candidate.resolve(strict=True)
    try:
        resolved_plan.relative_to(root)
    except ValueError as exc:
        raise FinisherError("ExecPlan is outside the repository") from exc
    if candidate.is_symlink() or resolved_plan.is_symlink():
        raise FinisherError("ExecPlan may not be a symlink")
    return root, resolved_plan


def _validate_paths(repo: Path, paths: Sequence[str], allowlist: Allowlist) -> None:
    for path in paths:
        safe = _safe_literal_path(path)
        if not _is_allowed(safe, allowlist.allowed):
            raise FinisherError(f"path outside allowlist: {safe}")
        reason = _forbidden_reason(safe, allowlist)
        if reason:
            raise FinisherError(f"forbidden path {safe!r}: {reason}")
        candidate = repo / safe
        if candidate.is_symlink():
            raise FinisherError(f"symlink rejected: {safe}")
        if candidate.exists():
            resolved = candidate.resolve()
            try:
                resolved.relative_to(repo)
            except ValueError as exc:
                raise FinisherError(f"path escapes repository: {safe}") from exc
            if candidate.is_file() and _SECRET_RE.search(candidate.read_bytes()):
                raise FinisherError(f"probable secret detected in {safe!r}")


def _validate_staged_entries(
    repo: Path,
    paths: Sequence[str],
    allowlist: Allowlist,
    report: Report,
    *,
    env: dict[str, str] | None = None,
) -> None:
    _validate_paths(repo, paths, allowlist)
    if not paths:
        return
    index = _run(
        repo, ("git", "ls-files", "-s", "-z", "--", *paths), report, env=env
    ).stdout
    modes: dict[str, str] = {}
    for record in index.split("\0"):
        if not record:
            continue
        metadata, separator, path = record.partition("\t")
        if not separator:
            raise FinisherError("unexpected staged index record")
        modes[path] = metadata.split(" ", maxsplit=1)[0]
    for path in paths:
        if modes.get(path) == "120000":
            raise FinisherError(f"staged symlink rejected: {path}")
        completed = subprocess.run(
            ("git", "show", f":{path}"),
            cwd=repo,
            capture_output=True,
            check=False,
            env=env,
        )
        report.commands.append(
            {
                "command": ["git", "show", f":{path}"],
                "returncode": completed.returncode,
            }
        )
        if completed.returncode != 0:
            raise FinisherError(f"cannot inspect staged content for {path!r}")
        if _SECRET_RE.search(completed.stdout):
            raise FinisherError(f"probable secret detected in staged {path!r}")


def _validate_declared_paths(repo: Path, allowlist: Allowlist) -> None:
    for entry in allowlist.allowed:
        candidate = repo / entry
        if not candidate.exists():
            raise FinisherError(f"allowlist path does not exist: {entry}")
        if candidate.is_symlink():
            raise FinisherError(f"allowlist path is a symlink: {entry}")


def _run_validations(
    repo: Path,
    validators: Sequence[Sequence[str]],
    report: Report,
) -> None:
    for command in validators:
        completed = _run(repo, command, report, check=False)
        result = {"command": list(command), "returncode": completed.returncode}
        report.validations.append(result)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            suffix = f": {detail}" if detail else ""
            raise FinisherError(f"validation failed: {' '.join(command)}{suffix}")
    tracked_data = _run(repo, ("git", "ls-files", "--", "data"), report).stdout
    if tracked_data.strip():
        raise FinisherError("Git tracks files below data/")
    report.validations.append(
        {"command": ["git", "ls-files", "--", "data"], "returncode": 0}
    )


def _staged_paths(
    repo: Path, report: Report, *, env: dict[str, str] | None = None
) -> list[str]:
    output = _run(
        repo, ("git", "diff", "--cached", "--name-only", "-z"), report, env=env
    ).stdout
    return sorted(path for path in output.split("\0") if path)


def _unstaged_tracked_paths(repo: Path, report: Report) -> list[str]:
    output = _run(repo, ("git", "diff", "--name-only", "-z"), report).stdout
    return sorted(path for path in output.split("\0") if path)


def _inspect(
    repo: Path,
    allowlist: Allowlist,
    validators: Sequence[Sequence[str]],
    report: Report,
) -> list[str]:
    _validate_declared_paths(repo, allowlist)
    tracked, untracked, ignored = _status(repo, report)
    report.modified_tracked = tracked
    report.untracked = untracked
    relevant_ignored = [
        path
        for path in ignored
        if _is_allowed(path, allowlist.allowed)
        or _hard_forbidden_reason(path) is not None
    ]
    collapsed_ignored: set[str] = set()
    for path in relevant_ignored:
        if "/__pycache__/" in path:
            collapsed_ignored.add(path.split("/__pycache__/", 1)[0] + "/__pycache__/")
        elif path.startswith(
            ("data/", "models/", "artifacts/", "predictions/", "runs/")
        ):
            collapsed_ignored.add(path.split("/", 1)[0] + "/")
        else:
            collapsed_ignored.add(path)
    report.ignored_relevant = sorted(collapsed_ignored)
    changed = sorted(set(tracked + untracked))
    report.in_scope = [path for path in changed if _is_allowed(path, allowlist.allowed)]
    report.out_of_scope = [path for path in changed if path not in report.in_scope]
    report.excluded = sorted(set(report.out_of_scope + report.ignored_relevant))
    if report.out_of_scope:
        raise FinisherError(
            "working tree contains paths outside the milestone allowlist: "
            + ", ".join(report.out_of_scope)
        )
    _validate_paths(repo, report.in_scope, allowlist)
    staged = _staged_paths(repo, report)
    report.staged = staged
    _validate_staged_entries(repo, staged, allowlist, report)
    _run_validations(repo, validators, report)
    return report.in_scope


def finish(
    repo: Path,
    plan: Path,
    mode: str,
    *,
    message: str | None = None,
    validators: Sequence[Sequence[str]] | None = None,
) -> Report:
    """Run a finishing mode; injectable validators keep temp-repo tests focused."""
    report = Report(mode=mode, plan=str(plan))
    try:
        root, resolved_plan = _assert_repo(repo.resolve(), plan)
        report.plan = resolved_plan.relative_to(root).as_posix()
        allowlist = parse_allowlist(resolved_plan)
        report.initial_commit = _run(
            root, ("git", "rev-parse", "HEAD"), report
        ).stdout.strip()
        if validators is None:
            _validate_tool_availability()
            validators = _default_validators()
        in_scope = _inspect(root, allowlist, validators, report)

        if mode == "check":
            pass
        elif mode == "stage":
            if not in_scope:
                raise FinisherError("no in-scope working-tree changes to stage")
            with tempfile.TemporaryDirectory(prefix="cop-finisher-index-") as temp:
                temporary_env = os.environ.copy()
                temporary_env["GIT_INDEX_FILE"] = str(Path(temp) / "index")
                _run(root, ("git", "read-tree", "HEAD"), report, env=temporary_env)
                _run(
                    root,
                    ("git", "add", "--", *in_scope),
                    report,
                    env=temporary_env,
                )
                _run(
                    root,
                    ("git", "diff", "--cached", "--check"),
                    report,
                    env=temporary_env,
                )
                temporary_staged = _staged_paths(root, report, env=temporary_env)
                _validate_staged_entries(
                    root,
                    temporary_staged,
                    allowlist,
                    report,
                    env=temporary_env,
                )
            _run(root, ("git", "add", "--", *in_scope), report)
            _run(root, ("git", "diff", "--cached", "--check"), report)
            report.staged = _staged_paths(root, report)
            _validate_staged_entries(root, report.staged, allowlist, report)
            report.staged_diff = _run(
                root, ("git", "diff", "--cached", "--name-status"), report
            ).stdout.splitlines()
        elif mode == "commit":
            if not message:
                raise FinisherError("--commit requires an explicit --message")
            if message != allowlist.expected_message:
                raise FinisherError("commit message does not match the ExecPlan")
            report.staged = _staged_paths(root, report)
            if not report.staged:
                raise FinisherError("nothing is staged")
            if set(report.staged) != set(in_scope):
                raise FinisherError(
                    "staged paths do not exactly match current in-scope changes"
                )
            if _unstaged_tracked_paths(root, report):
                raise FinisherError("working tree has unstaged tracked changes")
            _validate_staged_entries(root, report.staged, allowlist, report)
            _run(root, ("git", "diff", "--cached", "--check"), report)
            report.staged_diff = _run(
                root, ("git", "diff", "--cached", "--name-status"), report
            ).stdout.splitlines()
            _run(root, ("git", "commit", "-m", message), report)
            report.commit_created = _run(
                root, ("git", "rev-parse", "HEAD"), report
            ).stdout.strip()
        else:
            raise FinisherError(f"unknown mode: {mode}")

        report.ok = True
    except (FinisherError, OSError, UnicodeError) as exc:
        report.error = str(exc)
    finally:
        completed = subprocess.run(
            ("git", "status", "--short"),
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        report.commands.append(
            {
                "command": ["git", "status", "--short"],
                "returncode": completed.returncode,
            }
        )
        if completed.returncode == 0:
            report.final_status = completed.stdout.splitlines()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--stage", action="store_true")
    modes.add_argument("--commit", action="store_true")
    parser.add_argument("--message")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    mode = "check" if args.check else "stage" if args.stage else "commit"
    report = finish(Path.cwd(), args.plan, mode, message=args.message)
    json.dump(asdict(report), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
