# AGENTS.md

This is a beginner-friendly personal briefing agent project.

## Goals

Build a local-only Python CLI agent that helps summarize mock emails and mock Jira tasks.

## Safety rules

- Do not connect to real Outlook, Microsoft Graph, Jira, Slack, or other external services unless explicitly requested.
- Do not add OAuth, API keys, tokens, or secrets.
- Do not send emails, modify Jira tickets, or perform external actions.
- Prefer dry-run behavior and human-readable output.
- Keep an audit log for every classification decision.

## Engineering style

- Keep modules small and readable.
- Prefer deterministic logic before adding LLM calls.
- Add tests for classification and summary generation.
- Keep the CLI simple.
- Explain major design choices in README.md.

## Commands

Run tests:

```bash
python -m pytest
```

## Git workflow

- Make one commit per completed milestone.
- Before committing, run:
  - python -m pytest
  - python -m briefing_agent.cli when relevant
- Use clear, short commit messages.
- Do not rewrite git history unless explicitly asked.
- Do not commit secrets, credentials, tokens, or local environment files.
