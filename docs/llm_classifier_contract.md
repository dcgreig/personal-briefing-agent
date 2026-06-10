# LLM Classifier Contract

This document describes the intended contract for a future LLM-assisted
classifier. It is documentation only. The project must continue to use
`RuleBasedClassifier` by default, and no real LLM calls, SDKs, credentials,
prompts, environment variables, or network requests are part of this contract.

## Purpose

The future LLM-assisted classifier may help classify normalized briefing items
when deterministic rules are not enough. It must remain a classifier only. It
must not send emails, create drafts, update Jira, archive messages, modify
tasks, schedule jobs, or perform external actions.

## Input Shape

The classifier input should be one normalized `BriefingItem` plus the allowed
classification labels:

```json
{
  "run_id": "example-run-001",
  "item": {
    "item_id": "email-001",
    "source_type": "email",
    "source_name": "mock_email",
    "title": "Can you review the launch copy?",
    "body": "Please review the draft and send feedback when you can.",
    "metadata": {
      "sender": "priya@example.com",
      "received_at": "2026-06-09T09:20:00-04:00",
      "importance": "normal"
    }
  },
  "allowed_classifications": ["urgent", "waiting_on_me", "fyi", "ignore"],
  "safety": {
    "dry_run_only": true,
    "no_external_actions": true
  }
}
```

The future adapter should pass only the fields needed for classification. It
should not include secrets, access tokens, credentials, or unnecessary personal
data.

## Output Shape

The expected output is one JSON object:

```json
{
  "item_id": "email-001",
  "classification": "waiting_on_me",
  "rationale": "The item directly asks for review and feedback.",
  "confidence": 0.87,
  "uncertainty": "low"
}
```

Required fields:

- `item_id`: must match the input item id.
- `classification`: must be one of the allowed classifications.
- `rationale`: must be a non-empty human-readable reason.
- `confidence`: must be a number from `0.0` to `1.0`.
- `uncertainty`: must be one of `low`, `medium`, or `high`.

## Allowed Classifications

The only allowed classification labels are:

- `urgent`
- `waiting_on_me`
- `fyi`
- `ignore`

Any other label must be rejected.

## Rationale

The rationale should explain why the item received the classification. It
should be short, specific, and suitable for an audit log. Empty rationales or
generic rationales such as "classified by model" should be rejected.

## Confidence Expectations

Confidence must be a numeric score between `0.0` and `1.0`.

Suggested future handling:

- `0.80` to `1.00`: acceptable if the output is otherwise valid.
- `0.60` to `0.79`: acceptable only with human review.
- below `0.60`: treat as uncertain and fall back to the rule-based classifier.

These thresholds are guidance for a future implementation. They are not active
runtime behavior today.

## Uncertainty Handling

The `uncertainty` field should be:

- `low`: the classification is straightforward.
- `medium`: the item may need human review.
- `high`: the classifier is unsure and should fall back to deterministic logic
  or ask for human review.

High uncertainty should never trigger external actions.

## Safety Constraints

The future LLM-assisted classifier must:

- stay read-only and dry-run by default;
- classify only, not act;
- avoid real Outlook, Microsoft Graph, Jira, or other network calls inside the
  classifier;
- avoid SDKs, API keys, credentials, tokens, and environment variables until a
  separate integration milestone explicitly adds them;
- return structured output that can be validated before use;
- preserve auditability by keeping the rationale and confidence score.

## Fallback Behavior

If the LLM-assisted output is missing required fields, uses an invalid
classification, has an invalid confidence score, has high uncertainty, or cannot
be parsed, the future implementation should fail closed. Safe fallback options
are:

1. Use `RuleBasedClassifier`.
2. Mark the item for human review.
3. Log why the LLM-assisted result was rejected.

The current `LlmAssistedClassifier` placeholder does not classify anything. It
raises a clear not-implemented error and tells users to use
`classifier_mode = "rule_based"`.
