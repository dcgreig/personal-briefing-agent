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

```powershell
python -m briefing_agent.cli
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

After the briefing is printed, the CLI shows each classified item one at a time.
Press Enter to accept the suggested classification, or type one of these
categories to override it:

- `urgent`
- `waiting_on_me`
- `fyi`
- `ignore`

The audit log records the original classification, your final classification,
whether you changed it, the dry-run suggested action, and the `run_id` for the
CLI execution.

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
  models.py       # dataclasses used across the app
  review.py       # local human review prompts
  run_history.py  # JSONL run history writer
config/
  settings.toml
data/
  mock_emails.json
  mock_jira_tasks.json
tests/
  test_actions.py
  test_adapters.py
  test_audit.py
  test_config.py
  test_classifier.py
  test_review.py
  test_run_history.py
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
7. Save the briefing as Markdown if `briefing_output_path` is configured.
8. Ask you to accept or override each classification if `require_human_review` is true.
9. Generate one deterministic dry-run action suggestion for each finalized item.
10. Append one JSON object per reviewed item to the configured audit log.
11. Append one JSON object for the whole run to the configured run history log.

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
```

If the file is missing, the app uses those same defaults.

The fields mean:

- `enabled_sources`: which local adapters to run. Supported values are `mock_email` and `mock_jira`.
- `classifier_mode`: which classifier to use. Supported values are `rule_based` and `llm_assisted`.
- `require_human_review`: when `true`, the CLI asks you to approve or override each classification.
- `audit_log_path`: where JSONL audit records are appended.
- `run_history_path`: where one JSONL record per CLI execution is appended.
- `briefing_output_path`: where the latest Markdown briefing is saved. Set it to an empty string to skip file output.
- `lookback_hours`: a source-setting placeholder for future adapters. The current mock adapters keep all sample records loaded so the tutorial remains stable.

Each run history record includes the run id, generated timestamp, enabled
sources, total item count, counts by classification, Markdown briefing path, and
audit log path. The same run id is printed in the terminal, written to the
Markdown briefing, and included in every audit log entry for that run.

You can still override the audit path for a single run:

```powershell
python -m briefing_agent.cli --audit-log logs/test_audit.jsonl
```
