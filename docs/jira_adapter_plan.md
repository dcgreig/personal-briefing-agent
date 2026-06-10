# Jira Read-Only Adapter Plan

This document describes a future Jira task adapter. It is a planning document
only. The current project remains local-only and does not include Jira SDKs,
OAuth, credentials, API keys, environment variables, network calls, or live
Jira access.

## Where It Fits

The existing source adapter pattern is:

```text
source-specific data -> adapter -> BriefingItem -> classifier -> review -> audit
```

A future Jira adapter would sit next to the current local adapters:

- `MockEmailAdapter`
- `MockJiraAdapter`
- future `JiraTaskAdapter`

The adapter's responsibility would be narrow: read Jira issue fields in a
read-only way, then normalize each issue into a `BriefingItem`. Classification,
human review, dry-run action suggestions, Markdown output, audit logging, and
run history should continue to use the existing pipeline.

## Expected Input

The future adapter would receive read-only Jira issue data from a separate
integration layer. Conceptually, each issue would need fields like:

```json
{
  "id": "10001",
  "key": "PBA-201",
  "summary": "Review classifier copy",
  "description": "Tighten the wording for classification reasons.",
  "assignee": {
    "display_name": "David",
    "account_id": "example-account-id"
  },
  "reporter": {
    "display_name": "Priya"
  },
  "status": "To Do",
  "priority": "Medium",
  "due_date": "2026-06-14",
  "updated_at": "2026-06-10T09:00:00-04:00",
  "issue_type": "Task"
}
```

This shape is illustrative only. No live Jira calls exist in this repo.

## Expected Output

The adapter should return normalized `BriefingItem` objects:

```json
{
  "item_id": "jira-issue-10001",
  "source_type": "jira",
  "source_name": "jira_tasks",
  "title": "PBA-201: Review classifier copy",
  "body": "Tighten the wording for classification reasons.",
  "metadata": {
    "key": "PBA-201",
    "assignee": "me",
    "assignee_display_name": "David",
    "reporter": "Priya",
    "status": "To Do",
    "priority": "Medium",
    "due_date": "2026-06-14",
    "updated_at": "2026-06-10T09:00:00-04:00",
    "issue_type": "Task"
  }
}
```

The rest of the agent should not need to know whether the task came from mock
JSON or Jira. It should only receive `BriefingItem` objects.

## Field Mapping

Suggested mapping from Jira issue fields to `BriefingItem`:

- Issue id or key -> `item_id`
- Constant `jira` -> `source_type`
- Constant `jira_tasks` -> `source_name`
- Issue key plus summary -> `title`
- Description or summary fallback -> `body`
- Issue key -> `metadata.key`
- Assignee -> `metadata.assignee`
- Assignee display name -> `metadata.assignee_display_name`
- Reporter display name -> `metadata.reporter`
- Status -> `metadata.status`
- Priority -> `metadata.priority`
- Due date -> `metadata.due_date`
- Updated timestamp -> `metadata.updated_at`
- Issue type -> `metadata.issue_type`

The adapter should avoid storing unnecessary issue data. Prefer the smallest
read-only subset needed for classification and auditability.

## Read-Only Behavior

The future Jira adapter must be read-only. It must not:

- create issues;
- edit fields;
- assign or unassign issues;
- transition workflow status;
- comment on issues;
- close or reopen issues;
- add labels;
- change priority;
- log work;
- modify watchers or notifications.

Human review must remain required before any future action-oriented feature.
Even after review, this project should continue to treat Jira action output as
dry-run suggestions unless a separate milestone explicitly adds safe execution
behavior.

## Proposed Future Config

This is a proposed future config shape only. It is not active today.

```toml
[sources.jira_tasks]
enabled = false
source_name = "jira_tasks"
jql = "assignee = currentUser() AND statusCategory != Done"
saved_filter_name = ""
assigned_to_me_only = true
include_watched = false
max_items = 50
lookback_hours = 72
```

Possible fields:

- `source_name`: adapter name used in `BriefingItem.source_name`.
- `jql`: explicit read-only Jira query.
- `saved_filter_name`: named saved filter to read instead of raw JQL.
- `assigned_to_me_only`: whether to include only issues assigned to the user.
- `include_watched`: whether to include watched issues as context.
- `max_items`: maximum issues to normalize per run.
- `lookback_hours`: how far back to read recently updated issues.

When this is implemented later, the active config loader should validate these
values before the adapter runs.

## Safety Plan

Future Jira work must follow these constraints:

- Do not commit secrets, access tokens, refresh tokens, API tokens, client
  secrets, or local credential files.
- Use least-privilege permissions, ideally read-only Jira issue access scoped as
  narrowly as practical.
- Keep dry-run behavior as the default.
- Preserve audit logging for every classification and suggested action.
- Treat work tasks as sensitive. Avoid logging unnecessary issue descriptions,
  comments, or internal project details unless the user explicitly accepts that
  risk.
- Keep human review in the loop before any future action.
- Fail closed if permissions, token handling, or validation is unclear.

## Non-Goals For This Milestone

This milestone does not add:

- Jira SDKs;
- OAuth flows;
- API keys;
- environment variables;
- network calls;
- live Jira access;
- background jobs;
- issue creation, editing, assignment, transition, commenting, or closing.
