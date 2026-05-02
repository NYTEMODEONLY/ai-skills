# AI Skills

A collection of reusable AI agent skills for Claude Code, Codex, OpenClaw, and other assistants.

Each top-level folder is a standalone skill. The root README documents the full catalog, and each skill folder also includes its own README, `SKILL.md`, and supporting scripts or references.

## Skill Catalog

| Skill | What It Does | Main Requirements |
|-------|--------------|-------------------|
| [xai-x-link-reader](./xai-x-link-reader) | Resolves X.com/Twitter links through xAI Grok `x_search` tool calling when normal agents are blocked | Python 3.10+, `XAI_API_KEY` |
| [video-to-markdown-transcript](./video-to-markdown-transcript) | Transcribes videos into clean markdown with a captions-first workflow and Whisper fallback | `yt-dlp`, `ffmpeg`, optional `openai-whisper` |

## What are Skills?

Skills are reusable knowledge modules that teach AI agents how to perform specific workflows. A skill usually includes:

- `SKILL.md`: agent-facing instructions and trigger conditions
- `README.md`: human-facing documentation
- Supporting files: scripts, references, metadata, configs, or assets needed to execute the workflow

## Installing Skills

### Codex

```bash
mkdir -p ~/.codex/skills
cp -r xai-x-link-reader ~/.codex/skills/
cp -r video-to-markdown-transcript ~/.codex/skills/
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -r xai-x-link-reader ~/.claude/skills/
cp -r video-to-markdown-transcript ~/.claude/skills/
```

### OpenClaw

Skills are automatically loaded from `~/.openclaw/skills/` or can be synced from ClawHub.

```bash
mkdir -p ~/.openclaw/skills
cp -r xai-x-link-reader ~/.openclaw/skills/
cp -r video-to-markdown-transcript ~/.openclaw/skills/
```

### Manual Usage

Each skill folder contains standalone scripts that can be run directly. See the sections below and each folder README for exact commands.

## xai-x-link-reader

Folder: [xai-x-link-reader](./xai-x-link-reader)

### Purpose

Use `xai-x-link-reader` when a user gives an `x.com`, `twitter.com`, or `mobile.twitter.com` URL and the normal browser, crawler, or web search path cannot read the post. The skill routes the URL through xAI's Responses API with Grok's server-side `x_search` tool and returns a grounded extraction with citations when xAI provides them.

This skill is useful for:

- Reading an X post from a direct URL
- Pulling thread context, quoted posts, and repost context
- Summarizing X Articles without copying the full article
- Describing attached images or videos when requested
- Returning citations and tool-call metadata for traceability

### Requirements

- Python 3.10+
- xAI API key with Responses API and `x_search` access
- No Python package installation required

Set the key locally:

```bash
export XAI_API_KEY="your_xai_api_key_here"
```

Do not commit API keys, `.env` files, private post content, or user-sensitive screenshots.

### Quick Start

```bash
cd xai-x-link-reader
python3 scripts/fetch_x_link.py "https://x.com/xai/status/1234567890"
```

Add extraction instructions:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --query "include parent post, child replies, quoted post, and media context"
```

Return JSON:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --json
```

Inspect the request without calling xAI:

```bash
python3 scripts/fetch_x_link.py \
  "https://x.com/xai/status/1234567890" \
  --dry-run
```

### CLI Options

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

Environment variables:

| Variable | Purpose |
|----------|---------|
| `XAI_API_KEY` | Required xAI API key |
| `XAI_X_LINK_MODEL` | Optional model override |
| `XAI_API_BASE` | Optional API base override |

### Output Shape

Markdown mode returns extracted content, citations, exposed tool-call metadata, and usage when present.

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

### Failure Modes

- Missing key: set `XAI_API_KEY` locally and rerun.
- Model unavailable: pass `--model` or set `XAI_X_LINK_MODEL`.
- Tool unavailable: confirm the xAI account has access to Responses API tools and `x_search`.
- Private, deleted, or unavailable post: report that the exact content could not be retrieved and ask for a screenshot or pasted text only after the xAI path fails.

### Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing trigger conditions and workflow |
| `README.md` | Human-facing usage documentation |
| `agents/openai.yaml` | Codex UI metadata |
| `scripts/fetch_x_link.py` | Standard-library REST CLI for xAI Responses API and `x_search` |
| `references/xai-api-notes.md` | API payload, tools, citations, and failure notes |
| `LICENSE` | MIT license |

## video-to-markdown-transcript

Folder: [video-to-markdown-transcript](./video-to-markdown-transcript)

### Purpose

Use `video-to-markdown-transcript` to convert videos into clean, readable markdown transcripts. The skill follows a captions-first workflow: extract existing platform captions before falling back to local Whisper transcription.

This skill is useful for:

- Transcribing YouTube, Rumble, Vimeo, Coursera, Udemy, and similar video URLs
- Converting local video or audio files into text
- Creating lecture notes or study material from video content
- Producing readable markdown without subtitle timestamps or one-line caption fragments

### Requirements

Required:

```bash
brew install yt-dlp ffmpeg
```

Optional Whisper fallback:

```bash
pip install openai-whisper
```

Linux example:

```bash
pip install yt-dlp openai-whisper
sudo apt install ffmpeg
```

### Quick Start

```bash
cd video-to-markdown-transcript
chmod +x transcribe.sh
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

With options:

```bash
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --lang es
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --output "lecture-notes"
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --model large
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --fast
```

Modes:

- Default: use Whisper for best-quality punctuation and paragraph flow after preparing audio.
- `--fast`: extract existing subtitles for instant output when captions are available.

### SRT/VTT Converter

Convert an existing subtitle file to markdown:

```bash
python3 srt_to_markdown.py video.en.srt "Video Title"
python3 srt_to_markdown.py video.en.srt "Video Title" --timestamps
python3 srt_to_markdown.py video.en.srt "Video Title" --output notes.md
python3 srt_to_markdown.py video.en.srt --sentences 2
```

### Captions-First Pipeline

```text
Video URL or file
       |
       v
Try manual subtitles with yt-dlp
       |
       v
Try auto-generated subtitles
       |
       v
Download audio and transcribe with Whisper if no captions exist
       |
       v
Convert SRT/VTT to clean markdown
       |
       v
transcript.md
```

### Supported Platforms

| Platform | Subtitles Available | Auth Required |
|----------|---------------------|---------------|
| YouTube | Almost always, including auto-generated captions | No |
| Rumble | Sometimes | No |
| Vimeo | Often | No |
| Coursera | Usually high-quality manual captions | Often |
| Udemy | Usually high-quality manual captions | Often |
| Teachable | Sometimes | Often |
| Kajabi | Sometimes | Often |
| Local files | Use Whisper fallback | No |

For authenticated platforms:

```bash
yt-dlp --cookies-from-browser chrome --write-subs --skip-download "URL"
```

### Whisper Model Guide

| Model | Size | Relative Speed | Quality | Best For |
|-------|------|----------------|---------|----------|
| `tiny` | 39M | ~32x | Basic | Quick drafts |
| `base` | 74M | ~16x | Good | Short, clear audio |
| `small` | 244M | ~6x | Better | General use |
| `medium` | 769M | ~2x | Great | Important content |
| `turbo` | 809M | ~8x | Great | Default speed/quality tradeoff |
| `large` | 1550M | ~1x | Best | Critical accuracy |

### Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing trigger conditions and workflow |
| `README.md` | Human-facing usage documentation |
| `transcribe.sh` | Full video URL/file to markdown pipeline |
| `srt_to_markdown.py` | SRT/VTT to clean markdown converter |
| `moltuni-readme.md` | Moltuni marketplace copy |
| `moltuni-submission.json` | Moltuni marketplace metadata |
| `LICENSE` | MIT license |

## Security

- Do not commit API keys, `.env` files, cookies, private user data, generated transcripts from sensitive material, or generated cache files.
- API-backed skills should read secrets from environment variables.
- Authenticated `yt-dlp` workflows may use browser cookies; treat those outputs and commands as local-only unless intentionally publishing sanitized examples.

## Contributing

Fork the repo and submit pull requests with new skills or improvements. Keep each skill self-contained in its own top-level folder and include a folder-level README.

## License

MIT. See each skill folder for its license file.

---

Built by [NYTEMODE](https://nytemode.com)
