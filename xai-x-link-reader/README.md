# xAI X Link Reader

A Codex-compatible skill and standard-library Python CLI for resolving X.com/Twitter links through xAI's Grok tool calling.

Use this when a user gives an `x.com`, `twitter.com`, or `mobile.twitter.com` URL and the normal browser, crawler, or web search path cannot read the post. The skill routes the URL through xAI's Responses API with Grok's server-side `x_search` tool, then returns a grounded extraction with citations when xAI provides them.

## Why This Exists

X.com often blocks ordinary agent browsing and unauthenticated scraping. Grok's xAI API has server-side X Search tooling that can resolve posts, threads, profiles, media context, and X Articles more reliably than generic web fetchers.

This skill gives other agents a repeatable way to:

- Read an X post from a direct URL
- Pull thread context, quoted posts, and repost context
- Summarize X Articles without copying the full article
- Describe images or videos attached to a post when requested
- Return citations and tool-call metadata for traceability

## Requirements

- Python 3.10+
- An xAI API key with access to the Responses API and `x_search`
- No Python package installation required

Set the key in your local environment:

```bash
export XAI_API_KEY="your_xai_api_key_here"
```

Do not paste real API keys into chats, README files, examples, or commits.

## Quick Start

From this folder:

```bash
python3 scripts/fetch_x_link.py "https://x.com/xai/status/1234567890"
```

With extra extraction instructions:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --query "include parent post, child replies, quoted post, and media context"
```

Return JSON for another script or agent:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --json
```

Inspect the request payload without calling xAI:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --dry-run
```

## CLI Options

| Option | Purpose |
|--------|---------|
| `--query TEXT` | Add task-specific extraction instructions |
| `--json` | Emit a machine-readable response envelope |
| `--include-raw` | Include the raw xAI response in JSON mode |
| `--web-search` | Also enable xAI `web_search` for external article context |
| `--no-image-understanding` | Disable image understanding for faster/cheaper calls |
| `--video-understanding` | Enable video understanding for X Search |
| `--model MODEL` | Override the model, defaulting to `grok-4.3` |
| `--api-base URL` | Override the API base, defaulting to `https://api.x.ai/v1` |
| `--api-key-env NAME` | Read the API key from a different environment variable |
| `--max-output-tokens N` | Control max response length |
| `--dry-run` | Print the payload without making an API call |

Environment variable overrides:

| Variable | Purpose |
|----------|---------|
| `XAI_API_KEY` | Required xAI API key |
| `XAI_X_LINK_MODEL` | Optional model override |
| `XAI_API_BASE` | Optional API base override |

## As a Codex Skill

Copy the full folder into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -r xai-x-link-reader ~/.codex/skills/
```

Then invoke it naturally:

```text
Use $xai-x-link-reader to summarize this X post: https://x.com/...
```

The skill should trigger for requests like:

- "What does this X post say?"
- "Use this tweet as context for the implementation"
- "Summarize this X Article"
- "Check the thread behind this x.com link"
- "Pull the quoted post and media context from this tweet"

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing skill instructions |
| `agents/openai.yaml` | Codex UI metadata |
| `scripts/fetch_x_link.py` | REST CLI for xAI Responses API and `x_search` |
| `references/xai-api-notes.md` | Notes on xAI API payloads, tools, citations, and failures |

## Output Shape

Markdown mode returns:

- `Extracted Content`: summary, post details, thread/context, media/links, and reliability notes
- `Citations`: URLs returned by xAI's tool execution
- `Tool Calls`: exposed server-side tool-call metadata
- `Usage`: token/source usage when present

JSON mode returns:

```json
{
  "url": "https://x.com/...",
  "warning": null,
  "response_id": "resp_...",
  "model": "grok-4.3",
  "output_text": "...",
  "citations": ["https://x.com/i/status/..."],
  "tool_calls": [],
  "usage": {}
}
```

## Failure Modes

- Missing API key: set `XAI_API_KEY` locally and rerun.
- Model unavailable: pass `--model` or set `XAI_X_LINK_MODEL` to a model enabled for your xAI account.
- Tool unavailable: confirm the API key has access to xAI Responses API tools and `x_search`.
- Private/deleted/unavailable post: the script should report that the exact content could not be retrieved. Ask the user for a screenshot or pasted text only after this path fails.

## Security

- The script reads secrets from environment variables only.
- The script sends `store: false` in the xAI request payload by default.
- `.env` files and Python caches are ignored by this repo.
- Never commit real API keys, raw private post content, or user-sensitive screenshots.

## References

- [xAI X Search docs](https://docs.x.ai/developers/tools/x-search)
- [xAI Web Search docs](https://docs.x.ai/developers/tools/web-search)
- [xAI Citations docs](https://docs.x.ai/developers/tools/citations)
- [xAI Responses API comparison](https://docs.x.ai/developers/model-capabilities/text/comparison)

## License

MIT

---

Built by [nytemode](https://nytemode.com)
