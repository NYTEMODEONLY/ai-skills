#!/usr/bin/env python3
"""Fetch X.com/Twitter link context through xAI Responses API tools."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_API_BASE = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.3"

X_URL_RE = re.compile(
    r"(https?://)?(?:www\.)?(?:x\.com|twitter\.com|mobile\.twitter\.com)/[^\s<>'\"]+",
    re.IGNORECASE,
)


def extract_x_url(value: str) -> tuple[str, str | None]:
    match = X_URL_RE.search(value)
    if not match:
        return value.strip(), "Input does not look like an x.com/twitter.com URL; sending it anyway."

    url = match.group(0).rstrip(").,;]>")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url, None


def build_prompt(url: str, query: str | None) -> list[dict[str, str]]:
    extra = f"\nAdditional user request: {query.strip()}" if query else ""
    return [
        {
            "role": "system",
            "content": (
                "You extract information from X.com/Twitter links using xAI server-side tools. "
                "Use x_search to resolve the exact URL. If the exact link is deleted, private, "
                "unavailable, or ambiguous, state that clearly and do not invent details. "
                "Return concise Markdown with these sections: Summary, Post, Thread/Context, "
                "Media/Links, Reliability. Include author, handle, timestamp, post text, quoted "
                "or reposted content, X Article details, and media descriptions when available. "
                "For long-form articles, summarize rather than reproducing the full article."
            ),
        },
        {
            "role": "user",
            "content": f"Resolve and extract the content from this X/Twitter URL:\n{url}{extra}",
        },
    ]


def build_payload(args: argparse.Namespace, url: str) -> dict[str, Any]:
    tools: list[dict[str, Any]] = [
        {
            "type": "x_search",
            "enable_image_understanding": args.image_understanding,
            "enable_video_understanding": args.video_understanding,
        }
    ]

    if args.web_search:
        web_tool: dict[str, Any] = {"type": "web_search"}
        if args.image_understanding:
            web_tool["enable_image_understanding"] = True
        tools.append(web_tool)

    return {
        "model": args.model,
        "input": build_prompt(url, args.query),
        "tools": tools,
        "include": ["no_inline_citations"],
        "store": False,
        "max_output_tokens": args.max_output_tokens,
    }


def post_json(url: str, api_key: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"xAI API HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"xAI API request failed: {exc.reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"xAI API returned non-JSON response: {body[:500]}") from exc


def extract_output_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    for item in response.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
    return "\n\n".join(parts)


def extract_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for item in response.get("output", []):
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in {
            "web_search_call",
            "x_search_call",
            "code_interpreter_call",
            "file_search_call",
            "mcp_call",
        }:
            calls.append(
                {
                    key: item.get(key)
                    for key in ("type", "name", "status", "arguments", "action")
                    if key in item
                }
            )
    return calls


def render_markdown(url: str, warning: str | None, response: dict[str, Any]) -> str:
    text = extract_output_text(response)
    citations = response.get("citations") or []
    tool_calls = extract_tool_calls(response)
    usage = response.get("usage")

    lines = [
        "# X Link Extraction",
        "",
        f"URL: {url}",
        f"Model: {response.get('model', '(unknown)')}",
        f"Response ID: {response.get('id', '(unknown)')}",
    ]
    if warning:
        lines.extend(["", f"Warning: {warning}"])

    lines.extend(["", "## Extracted Content", "", text or "(No output text returned.)"])

    lines.extend(["", "## Citations"])
    if citations:
        lines.extend(f"- {citation}" for citation in citations)
    else:
        lines.append("(No citations returned.)")

    lines.extend(["", "## Tool Calls"])
    if tool_calls:
        for call in tool_calls:
            rendered = json.dumps(call, ensure_ascii=False, sort_keys=True)
            lines.append(f"- `{rendered}`")
    else:
        lines.append("(No server-side tool calls exposed in response.)")

    if usage:
        lines.extend(["", "## Usage", "", "```json", json.dumps(usage, indent=2, sort_keys=True), "```"])

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve an X.com/Twitter link through xAI Grok x_search tool calling."
    )
    parser.add_argument("url", help="X.com/Twitter URL, or text containing one.")
    parser.add_argument("--query", help="Additional extraction instructions for Grok.")
    parser.add_argument("--model", default=os.getenv("XAI_X_LINK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-base", default=os.getenv("XAI_API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--api-key-env", default="XAI_API_KEY")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-output-tokens", type=int, default=1800)
    parser.add_argument("--web-search", action="store_true", help="Also enable xAI web_search.")
    parser.add_argument(
        "--no-image-understanding",
        dest="image_understanding",
        action="store_false",
        help="Disable image understanding for tool calls.",
    )
    parser.set_defaults(image_understanding=True)
    parser.add_argument(
        "--video-understanding",
        action="store_true",
        help="Enable video understanding for X search.",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON envelope instead of Markdown.")
    parser.add_argument("--include-raw", action="store_true", help="Include raw xAI response in JSON output.")
    parser.add_argument("--dry-run", action="store_true", help="Print the request payload without calling xAI.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    x_url, warning = extract_x_url(args.url)
    endpoint = urllib.parse.urljoin(args.api_base.rstrip("/") + "/", "responses")
    payload = build_payload(args, x_url)

    if args.dry_run:
        print(json.dumps({"endpoint": endpoint, "payload": payload, "warning": warning}, indent=2))
        return 0

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        print(
            f"Missing API key. Set {args.api_key_env} in the local environment; do not commit it.",
            file=sys.stderr,
        )
        return 2

    try:
        response = post_json(endpoint, api_key, payload, args.timeout)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        envelope: dict[str, Any] = {
            "url": x_url,
            "warning": warning,
            "response_id": response.get("id"),
            "model": response.get("model"),
            "output_text": extract_output_text(response),
            "citations": response.get("citations") or [],
            "tool_calls": extract_tool_calls(response),
            "usage": response.get("usage"),
        }
        if args.include_raw:
            envelope["raw_response"] = response
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(x_url, warning, response), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
