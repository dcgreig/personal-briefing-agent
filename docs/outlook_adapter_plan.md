# Outlook Read-Only Adapter Plan

This document describes a future Outlook work email adapter. It is a planning
document only. The current project remains local-only and does not include
Microsoft Graph, OAuth, credentials, API keys, environment variables, network
calls, or live Outlook access.

## Where It Fits

The existing source adapter pattern is:

```text
source-specific data -> adapter -> BriefingItem -> classifier -> review -> audit
```

A future Outlook adapter would sit next to the current local adapters:

- `MockEmailAdapter`
- `MockJiraAdapter`
- future `OutlookEmailAdapter`

The adapter's responsibility would be narrow: read work email metadata and
message text, then normalize each message into a `BriefingItem`. Classification,
human review, dry-run action suggestions, Markdown output, audit logging, and
run history should continue to use the existing pipeline.

## Expected Input

The future adapter would receive read-only Outlook email message data from a
separate integration layer. Conceptually, each message would need fields like:

```json
{
  "id": "outlook-message-id",
  "subject": "Can you review the launch plan?",
  "body_preview": "Please review the launch plan before Friday.",
  "from": {
    "email_address": "teammate@example.com",
    "name": "Teammate"
  },
  "received_at": "2026-06-10T13:00:00-04:00",
  "importance": "normal",
  "is_read": false,
  "folder": "Inbox"
}
```

This shape is illustrative only. No live Outlook calls exist in this repo.

## Expected Output

The adapter should return normalized `BriefingItem` objects:

```json
{
  "item_id": "outlook-message-id",
  "source_type": "email",
  "source_name": "outlook_email",
  "title": "Can you review the launch plan?",
  "body": "Please review the launch plan before Friday.",
  "metadata": {
    "sender": "teammate@example.com",
    "sender_name": "Teammate",
    "received_at": "2026-06-10T13:00:00-04:00",
    "importance": "normal",
    "is_read": "false",
    "folder": "Inbox"
  }
}
```

The rest of the agent should not need to know whether the email came from mock
JSON or Outlook. It should only receive `BriefingItem` objects.

## Field Mapping

Suggested mapping from Outlook-style message fields to `BriefingItem`:

- Message id -> `item_id`
- Constant `email` -> `source_type`
- Constant `outlook_email` -> `source_name`
- Subject -> `title`
- Body preview or plain-text body -> `body`
- Sender email -> `metadata.sender`
- Sender display name -> `metadata.sender_name`
- Received datetime -> `metadata.received_at`
- Importance -> `metadata.importance`
- Read status -> `metadata.is_read`
- Folder/mailbox scope -> `metadata.folder`

The adapter should avoid storing unnecessary message data. Prefer the smallest
read-only subset needed for classification and auditability.

## Read-Only Behavior

The future Outlook adapter must be read-only. It must not:

- send email;
- create drafts;
- delete messages;
- archive messages;
- move messages;
- label, tag, or categorize messages;
- mark messages read or unread;
- modify folders;
- modify tasks or calendar events.

Human review must remain required before any future action-oriented feature.
Even after review, this project should continue to treat action output as
dry-run suggestions unless a separate milestone explicitly adds safe execution
behavior.

## Proposed Future Config

This is a proposed future config shape only. It is not active today.

```toml
[sources.outlook_email]
enabled = false
source_name = "outlook_email"
lookback_hours = 24
unread_only = true
mailbox_scope = "Inbox"
max_items = 50
```

Possible fields:

- `source_name`: adapter name used in `BriefingItem.source_name`.
- `lookback_hours`: how far back to read messages.
- `unread_only`: whether to include only unread messages.
- `mailbox_scope`: which folder or mailbox view to read, such as `Inbox`.
- `max_items`: maximum messages to normalize per run.

When this is implemented later, the active config loader should validate these
values before the adapter runs.

## Safety Plan

Future Outlook work must follow these constraints:

- Do not commit secrets, access tokens, refresh tokens, client secrets, or local
  credential files.
- Use least-privilege Microsoft Graph permissions, ideally read-only mail access
  scoped as narrowly as practical.
- Keep dry-run behavior as the default.
- Preserve audit logging for every classification and suggested action.
- Treat work email as sensitive. Avoid logging full message bodies unless the
  user explicitly accepts that risk.
- Keep human review in the loop before any future action.
- Fail closed if permissions, token handling, or validation is unclear.

## Non-Goals For This Milestone

This milestone does not add:

- Microsoft Graph SDKs;
- OAuth flows;
- API keys;
- environment variables;
- network calls;
- live Outlook access;
- background jobs;
- email sending, drafting, deleting, archiving, moving, or labeling.
