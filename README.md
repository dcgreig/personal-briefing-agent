# Personal Briefing Agent

A small, beginner-friendly Python CLI that reads mock emails and mock Jira tasks
through local source adapters, classifies each item, prints a daily briefing,
and appends a JSONL audit log after a human review step.

This project is intentionally local-only:

- No Outlook, Microsoft Graph, Jira, or network API calls yet
- No secrets, API keys, OAuth, or environment variables
- Plain Python dataclasses and standard-library modules
- Simple classifier rules that are easy to inspect and change

## Quick Start

Normal interactive run:

```powershell
python -m briefing_agent.cli
```

Explicit run subcommand:

```powershell
python -m briefing_agent.cli run
```

Non-interactive run for tests or automation:

```powershell
python -m briefing_agent.cli --no-review
python -m briefing_agent.cli run --no-review
```

Show recent briefing runs:

```powershell
python -m briefing_agent.cli history
```

Show details for one run:

```powershell
python -m briefing_agent.cli show-run <run_id>
```

The CLI loads:

- `data/mock_emails.json`
- `data/mock_jira_tasks.json`
- `config/settings.toml`

It writes audit records to:

- `logs/audit.jsonl`

It writes one run-history record per CLI execution to:

- `logs/run_history.jsonl`

It also writes the latest briefing to a Markdown file:

- `logs/daily_briefing.md`

In a normal interactive run, the CLI prints the Daily Briefing, then shows each
classified item one at a time with its source, type, title, classification,
reason, suggested dry-run action, and action rationale. Press Enter to accept
the suggested classification, use a shortcut, or type one of these categories to
override it:

- `urgent`
- `waiting_on_me`
- `fyi`
- `ignore`

You can also type `skip` to keep the current classification and mark the item as
skipped for now. After all items are reviewed, the CLI shows a final confirmation
summary before writing the audit log, run history, and Markdown briefing.

Use `--no-review` to skip prompts and accept all classifications for that run.
This is useful for tests and automation, and still stays local-only.

The audit log records the original classification, your final classification,
whether you changed it, whether you skipped it for now, the dry-run suggested
action, and the `run_id` for the CLI execution.

The Markdown briefing includes:

- `# Daily Briefing`
- the `run_id`
- a generated timestamp
- summary counts by classification
- sections for urgent, waiting-on-me, FYI, and ignored items
- each item's title, source, type, classification, reason, and dry-run suggested action

## Running Tests

```powershell
python -m pytest
```

If `pytest` is not installed yet:

```powershell
python -m pip install -e ".[test]"
```

## Project Structure

```text
briefing_agent/
  actions.py      # deterministic dry-run action suggestions
  adapters.py     # local source adapters that produce BriefingItem objects
  audit.py        # JSONL audit log writer
  briefing.py     # terminal briefing formatting
  classifier.py   # classifier interface plus rule-based implementation
  cli.py          # python -m entry point
  config.py       # local TOML settings loader
  filters.py      # local include/exclude filters
  llm_contract.py # local validation helpers for future LLM output
  models.py       # dataclasses used across the app
  review.py       # local human review prompts
  run_history.py  # JSONL run history writer
config/
  settings.toml
data/
  mock_emails.json
  mock_jira_tasks.json
docs/
  jira_adapter_plan.md
  llm_classifier_contract.md
  outlook_adapter_plan.md
tests/
  test_actions.py
  test_adapters.py
  test_audit.py
  test_config.py
  test_classifier.py
  test_jira_plan_fixture.py
  test_llm_contract.py
  test_outlook_plan_fixture.py
  test_review.py
  test_run_history.py
  fixtures/
    sample_jira_briefing_item.json
    sample_outlook_briefing_item.json
    sample_llm_classifier_input.json
    sample_valid_llm_classifier_output.json
    sample_invalid_llm_classifier_output.json
logs/
  audit.jsonl          # generated when the CLI runs
  daily_briefing.md    # generated when the CLI runs
  run_history.jsonl    # generated when the CLI runs
```

## How The Agent Works

1. Load mock items from JSON.
2. Load local settings from `config/settings.toml`, or use defaults if the file is missing.
3. Use enabled source adapters to normalize source records into `BriefingItem` objects.
4. Run the classifier over those normalized `BriefingItem` objects.
5. Build a short summary and reason for each item.
6. Print a grouped "Daily Briefing" to the terminal.
7. Ask you to accept, override, or skip each classification if review is enabled.
8. Apply any final-classification filters.
9. Show a final confirmation summary before writing local output files.
10. Generate one deterministic dry-run action suggestion for each finalized item.
11. Save the briefing as Markdown if `briefing_output_path` is configured.
12. Append one JSON object per reviewed item to the configured audit log.
13. Append one JSON object for the whole run to the configured run history log.

When `--no-review` is used, the CLI accepts all classifications and skips the
interactive prompts and final confirmation.

The classifier returns one of four categories:

- `urgent`: time-sensitive, blocked, high priority, or needs attention today
- `waiting_on_me`: assigned to you or asking you for a response, review, or approval
- `fyi`: useful context but no direct action requested
- `ignore`: low-value, completed, canceled, automated, or promotional items

The rules live in `briefing_agent/classifier.py`. They are deliberately written
as readable Python conditionals so someone learning agentic development can see
exactly why the agent made each decision.

## Classifier Modes

The project has a classifier interface so multiple classifier implementations
can exist later. The supported config values are:

- `rule_based`: the default deterministic local classifier.
- `llm_assisted`: a scaffolded placeholder that fails safely because no LLM implementation exists yet.

`rule_based` remains the default because it is predictable, testable, local-only,
and does not require network calls, model calls, API keys, prompts, or secrets.
If `classifier_mode` is set to `llm_assisted`, the CLI stops with a clear
message explaining that LLM-assisted classification is scaffolded but not
implemented.

The future LLM classifier contract is documented in
`docs/llm_classifier_contract.md`. It describes the intended input shape, output
shape, allowed classifications, rationale and confidence requirements,
uncertainty handling, safety constraints, and fallback behavior. The repo also
includes JSON fixtures and local validation tests for that contract. These are
contract tests only; they do not execute prompts, model calls, SDK calls, or
network requests.

## Dry-Run Action Suggestions

After classification and human review, the agent suggests one possible next
action per finalized item. These suggestions are deterministic and local-only.
They are not executed.

Supported suggestion types are:

- `no_action`
- `review`
- `reply`
- `follow_up`
- `update_task`

Each suggestion includes an action type, title, rationale, and
`requires_human_approval`. Suggestions that imply external work, such as
replying to an email or updating a task, require human approval. The CLI only
prints and logs the suggestion; it does not send emails, create drafts, update
Jira, archive messages, modify tasks, or make network calls.

## Source Adapters

Input sources are represented by small adapters. An adapter is a lightweight
interface: it has one job, read from one source and return normalized
`BriefingItem` objects. The current adapters are local-only:

- `MockEmailAdapter` reads `data/mock_emails.json`
- `MockJiraAdapter` reads `data/mock_jira_tasks.json`

Future work email support should be added as a separate Outlook adapter. That
adapter should use Microsoft Graph read-only permissions, such as mail read
access only, and should not send, archive, delete, label, or modify messages.
OAuth, credentials, and real network calls are intentionally out of scope for
this local mock version.

The future Outlook read-only adapter plan is documented in
`docs/outlook_adapter_plan.md`. It explains where an Outlook adapter would fit,
how Outlook messages should map into `BriefingItem`, what fields are needed,
proposed future config ideas, and the safety requirements for work email. The
plan is documentation only; `outlook_email` is not an active source today.

The future Jira read-only adapter plan is documented in
`docs/jira_adapter_plan.md`. It explains where a Jira adapter would fit, how
Jira issues should map into `BriefingItem`, what fields are needed, proposed
future config ideas, and the safety requirements for work tasks. The plan is
documentation only; `jira_tasks` is not an active source today.

## Local Configuration

Settings live in `config/settings.toml`:

```toml
enabled_sources = ["mock_email", "mock_jira"]
classifier_mode = "rule_based"
require_human_review = true
audit_log_path = "logs/audit.jsonl"
run_history_path = "logs/run_history.jsonl"
briefing_output_path = "logs/daily_briefing.md"
lookback_hours = 24
include_sources = []
exclude_sources = []
include_item_types = []
exclude_item_types = []
include_classifications = []
exclude_classifications = []
max_items = 0
```

If the file is missing, the app uses those same defaults.

The fields mean:

- `enabled_sources`: which local adapters to run. Supported values are `mock_email` and `mock_jira`.
- `classifier_mode`: which classifier to use. Supported values are `rule_based` and `llm_assisted`.
- `require_human_review`: when `true`, the CLI asks you to approve or override each classification. Use `--no-review` to skip prompts for a single run.
- `audit_log_path`: where JSONL audit records are appended.
- `run_history_path`: where one JSONL record per CLI execution is appended.
- `briefing_output_path`: where the latest Markdown briefing is saved. Set it to an empty string to skip file output.
- `lookback_hours`: a source-setting placeholder for future adapters. The current mock adapters keep all sample records loaded so the tutorial remains stable.
- `include_sources`: optional source names to keep, such as `mock_email`.
- `exclude_sources`: optional source names to remove, such as `mock_jira`.
- `include_item_types`: optional item types to keep. Supported values are `email` and `jira`.
- `exclude_item_types`: optional item types to remove. Supported values are `email` and `jira`.
- `include_classifications`: optional final classifications to keep. Supported values are `urgent`, `waiting_on_me`, `fyi`, and `ignore`.
- `exclude_classifications`: optional final classifications to remove.
- `max_items`: maximum number of items to classify after source/type filters. Use `0` for no limit.

Source, item type, and `max_items` filters run before classification.
Classification filters run after classification and human review, so they use
the final reviewed classification. Filter settings are included in run history,
and the Markdown briefing includes a "Filters Applied" section.

Example: only mock email:

```toml
include_sources = ["mock_email"]
```

Example: exclude ignored items from the final briefing:

```toml
exclude_classifications = ["ignore"]
```

Example: classify at most five items:

```toml
max_items = 5
```

Each run history record includes the run id, generated timestamp, enabled
sources, total item count, counts by classification, Markdown briefing path, and
audit log path. It also includes the configured local filters. The same run id
is printed in the terminal, written to the Markdown briefing, and included in
every audit log entry for that run.

You can still override the audit path for a single run:

```powershell
python -m briefing_agent.cli --audit-log logs/test_audit.jsonl
```

The CLI also has local history commands:

- `python -m briefing_agent.cli history` reads the configured `run_history_path` and prints recent runs.
- `python -m briefing_agent.cli show-run <run_id>` prints details for one run.

If the run history file does not exist yet, or a requested run id is not found,
the CLI prints a friendly message and does not perform any external action.
