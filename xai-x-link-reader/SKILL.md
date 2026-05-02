---
name: xai-x-link-reader
description: Retrieve and summarize X.com/Twitter posts, threads, profiles, quoted posts, media context, and X Articles through xAI Grok tool calling when normal browsing cannot access the URL. Use when the user provides an x.com, twitter.com, or mobile.twitter.com link and asks Codex to inspect, parse, summarize, verify, cite, analyze, or use the linked X content as project context.
---

# xAI X Link Reader

## Overview

Use xAI's Responses API with Grok's server-side `x_search` tool to resolve X links that other agents or web fetchers cannot parse. Prefer the bundled script over ordinary browser/web scraping whenever the user gives an X.com or Twitter URL.

Never paste, store, or commit an xAI API key. Read it from `XAI_API_KEY` or another explicitly named environment variable.

## Quick Start

Run the script from this skill folder:

```bash
python3 scripts/fetch_x_link.py "https://x.com/user/status/123"
```

Useful options:

- `--query "include parent and child posts"` to steer extraction.
- `--web-search` when the X post points to external articles or the user asks for surrounding web context.
- `--json` when another tool or script needs machine-readable output.
- `--dry-run` to inspect the API payload without using an API key.
- `--model` or `XAI_X_LINK_MODEL` to override the default model.

If `XAI_API_KEY` is missing, ask the user to set it in their local environment. Do not ask them to paste the raw key into the chat.

## Workflow

1. Extract the X/Twitter URL from the user's prompt. Support `x.com`, `twitter.com`, and `mobile.twitter.com` links.
2. Run `scripts/fetch_x_link.py` with the URL and any task-specific `--query`.
3. Use the script's extracted content and citations in the answer or implementation work.
4. If Grok cannot access the exact link, say that clearly and avoid guessing. Ask for a screenshot or pasted content only when the xAI path fails.

For long-form X Articles, summarize the article and quote sparingly. For posts, include the author, handle, post text, timestamp, thread context, quoted/reposted content, media descriptions, links, and source citations when available.

## Script Contract

`scripts/fetch_x_link.py` uses only Python standard-library modules and calls:

```text
POST https://api.x.ai/v1/responses
```

It sends `store: false`, `include: ["no_inline_citations"]`, and enables the `x_search` server-side tool. It can optionally add `web_search`.

Environment variables:

- `XAI_API_KEY`: required API key.
- `XAI_X_LINK_MODEL`: optional model override.
- `XAI_API_BASE`: optional API base override; defaults to `https://api.x.ai/v1`.

## References

Read `references/xai-api-notes.md` before changing the payload, model, tool configuration, citation handling, or API error behavior.
