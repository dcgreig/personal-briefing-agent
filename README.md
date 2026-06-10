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
and whether you changed it.

The Markdown briefing includes:

- `# Daily Briefing`
- a generated timestamp
- summary counts by classification
- sections for urgent, waiting-on-me, FYI, and ignored items
- each item's title, source, type, classification, and reason

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
  adapters.py     # local source adapters that produce BriefingItem objects
  audit.py        # JSONL audit log writer
  briefing.py     # terminal briefing formatting
  classifier.py   # simple classification heuristics over BriefingItem
  cli.py          # python -m entry point
  config.py       # local TOML settings loader
  models.py       # dataclasses used across the app
  review.py       # local human review prompts
config/
  settings.toml
data/
  mock_emails.json
  mock_jira_tasks.json
tests/
  test_adapters.py
  test_audit.py
  test_config.py
  test_classifier.py
  test_review.py
logs/
  audit.jsonl          # generated when the CLI runs
  daily_briefing.md    # generated when the CLI runs
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
9. Append one JSON object per reviewed item to the configured audit log.

The classifier returns one of four categories:

- `urgent`: time-sensitive, blocked, high priority, or needs attention today
- `waiting_on_me`: assigned to you or asking you for a response, review, or approval
- `fyi`: useful context but no direct action requested
- `ignore`: low-value, completed, canceled, automated, or promotional items

The rules live in `briefing_agent/classifier.py`. They are deliberately written
as readable Python conditionals so someone learning agentic development can see
exactly why the agent made each decision.

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
require_human_review = true
audit_log_path = "logs/audit.jsonl"
briefing_output_path = "logs/daily_briefing.md"
lookback_hours = 24
```

If the file is missing, the app uses those same defaults.

The fields mean:

- `enabled_sources`: which local adapters to run. Supported values are `mock_email` and `mock_jira`.
- `require_human_review`: when `true`, the CLI asks you to approve or override each classification.
- `audit_log_path`: where JSONL audit records are appended.
- `briefing_output_path`: where the latest Markdown briefing is saved. Set it to an empty string to skip file output.
- `lookback_hours`: a source-setting placeholder for future adapters. The current mock adapters keep all sample records loaded so the tutorial remains stable.

You can still override the audit path for a single run:

```powershell
python -m briefing_agent.cli --audit-log logs/test_audit.jsonl
```
