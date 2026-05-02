# xAI API Notes

Checked against official xAI docs on 2026-05-02.

Official references:

- https://docs.x.ai/overview
- https://docs.x.ai/developers/tools/x-search
- https://docs.x.ai/developers/tools/web-search
- https://docs.x.ai/developers/tools/citations
- https://docs.x.ai/developers/model-capabilities/text/comparison

## API Choices

- Prefer the Responses API endpoint, `https://api.x.ai/v1/responses`.
- Use the OpenAI-compatible request shape with `model`, `input`, `tools`, and optional `include`.
- Use `store: false` by default so link extraction requests are not retained for conversation continuation.
- Default to `grok-4.3` as the model, but allow `XAI_X_LINK_MODEL` or `--model` because model names change.

## Tools

- Use `{"type": "x_search"}` for X.com/Twitter links. xAI documents this tool as supporting keyword search, semantic search, user search, and thread fetch on X.
- Add `enable_image_understanding: true` when the post may contain images.
- Add `enable_video_understanding: true` only when the user specifically needs video understanding.
- Add `{"type": "web_search"}` only when the user asks for web context around the X post or the X post links to external pages that need inspection.

## Citations

- Responses include a top-level `citations` list for sources encountered during successful tool execution.
- Inline citations are enabled by default for the Responses API. Use `include: ["no_inline_citations"]` when the output needs to be clean text or JSON.
- Structured citation annotations may also appear inside `output[*].content[*].annotations`.

## Common Failures

- Missing key: ask the user to set `XAI_API_KEY` in the local environment; do not ask for the raw key in chat.
- Model rejected: retry with `--model` or set `XAI_X_LINK_MODEL` to a model enabled for the key.
- Tool unavailable: confirm the account has access to xAI Responses API tools, especially `x_search`.
- Link unavailable/private/deleted: report that the exact content could not be retrieved and ask for a screenshot or pasted text.
