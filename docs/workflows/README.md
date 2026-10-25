# COP Wave and Task Workflow

The workflow is an English-first, repository-level coordination contract for
multi-agent implementation. It is not a claim that agents have already run.

Each workflow manifest defines:

- ordered Waves with explicit exit criteria;
- bounded Tasks with a single owner agent;
- dependencies between Tasks;
- allowed and prohibited paths;
- a task status that reflects the verified repository state.

The coordinator delegates a Task only when its dependencies are complete. The
assigned agent must stay within its path allowlist and return files changed,
commands, tests, findings, and unresolved risks. The reviewer remains
read-only. The milestone finisher runs closure validations and never commits
without explicit human authorization.

Validate the current Home Credit workflow with:

```bash
python3 scripts/validate_workflow.py
```

Inspect tasks that are ready for assignment without changing the manifest with:

```bash
python3 -m scripts.workflow_status
python3 -m scripts.workflow_status --agent data_ml --json
```

Only tasks with status `ready` whose dependencies have status `complete` are
returned. A task marked `complete_pending_review` is intentionally not treated
as complete, so downstream work cannot bypass independent review.

The manifest currently describes a proposed workflow. Its `blocked_on_*`
statuses are intentional: the next dataset gate has not been accepted or
executed yet.
