# Video to Markdown Transcript

A Claude Code skill and CLI toolset that transcribes any video into clean, readable markdown. Inspired by [Ditto Transcript Generator](https://dittotranscriptgenerator.com)'s "captions-first" philosophy.

## How It Works

**Captions-first, transcription-second.**

Most video platforms already have subtitles loaded -- either uploaded by the creator or auto-generated. This tool extracts those existing captions before falling back to AI transcription. This means:

- **Instant results** for most YouTube, Coursera, Udemy, and Rumble videos
- **No GPU required** for subtitle extraction
- **No API keys** -- everything runs locally
- **Clean output** -- timestamps stripped, lines merged into natural paragraphs

### The Pipeline

```
Video URL or File
       |
       v
  [1] Try manual subtitles (yt-dlp --write-subs)
       |
       v  (not found?)
  [2] Try auto-generated subs (yt-dlp --write-auto-subs)
       |
       v  (not found?)
  [3] Download audio + Whisper transcription
       |
       v
  [4] SRT/VTT --> Clean Markdown
       |
       v
  transcript.md
```

## Quick Start

### Prerequisites

```bash
# macOS
brew install yt-dlp ffmpeg
pip install openai-whisper    # optional, only for fallback

# Linux
pip install yt-dlp openai-whisper
sudo apt install ffmpeg
```

### Usage

**One-command pipeline:**

```bash
chmod +x transcribe.sh
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

**With options:**

```bash
# Spanish transcript
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --lang es

# Custom output name
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --output "lecture-notes"

# Use Whisper large model for best accuracy
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --model large

# Fast mode: use subtitles instead of Whisper (instant, no GPU needed)
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --fast
```

**Modes:**
- **Default**: Uses Whisper for best quality (punctuated sentences, proper paragraphs)
- **`--fast`**: Extracts existing subtitles (instant, but may lack punctuation for auto-generated subs)

**Python converter standalone:**

```bash
# Convert an existing SRT file to markdown
python3 srt_to_markdown.py video.en.srt "Video Title"

# With timestamp markers
python3 srt_to_markdown.py video.en.srt "Video Title" --timestamps

# Custom output path
python3 srt_to_markdown.py video.en.srt "Video Title" --output notes.md

# Fewer sentences per paragraph
python3 srt_to_markdown.py video.en.srt --sentences 2
```

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition (place in `~/.claude/skills/video-to-markdown-transcript/`) |
| `transcribe.sh` | Full pipeline: URL in, markdown out |
| `srt_to_markdown.py` | SRT/VTT to clean markdown converter |

## As a Claude Code Skill

Copy the `SKILL.md` to your Claude Code skills directory:

```bash
mkdir -p ~/.claude/skills/video-to-markdown-transcript
cp SKILL.md ~/.claude/skills/video-to-markdown-transcript/
```

Then Claude Code will automatically know how to transcribe videos when you ask things like:
- "Transcribe this video: https://..."
- "Get me a transcript of this lecture"
- "Convert this YouTube video to markdown notes"

## Supported Platforms

| Platform | Subtitles Available | Auth Required |
|----------|-------------------|---------------|
| YouTube | Almost always (auto-generated) | No |
| Rumble | Sometimes | No |
| Vimeo | Often | No |
| Coursera | Usually (high quality) | Yes (cookies) |
| Udemy | Usually (high quality) | Yes (cookies) |
| Teachable | Sometimes | Yes (cookies) |
| Kajabi | Sometimes | Yes (cookies) |
| Local files | N/A (use Whisper) | No |

For authenticated platforms:
```bash
yt-dlp --cookies-from-browser chrome --write-subs --skip-download "URL"
```

## Whisper Model Guide

When no subtitles exist and Whisper is used as fallback:

| Model | Size | Relative Speed | Quality | Best For |
|-------|------|----------------|---------|----------|
| tiny | 39M | ~32x | Basic | Quick drafts |
| base | 74M | ~16x | Good | Short, clear audio |
| small | 244M | ~6x | Better | General use |
| medium | 769M | ~2x | Great | Important content |
| **turbo** | **809M** | **~8x** | **Great** | **Default - best speed/quality tradeoff** |
| large | 1550M | ~1x | Best | Critical accuracy |

## Example Output

**Input**: A YouTube video about Bitcoin mining

**Output** (`transcript.md`):
```markdown
# Bitcoin Mining Explained

> Source: https://www.youtube.com/watch?v=example

Welcome to this presentation about Bitcoin mining and how it works.
Today we're going to cover three main topics that will help you
understand the fundamentals of proof-of-work consensus.

First, let's talk about what mining actually is. At its core, mining
is the process of adding transaction records to Bitcoin's public
ledger. Miners compete to solve computational puzzles, and the winner
gets to add the next block to the chain.
```

## Credits

- Inspired by [Ditto Transcript Generator](https://dittotranscriptgenerator.com) ([BitcoinTalk thread](https://bitcointalk.org/index.php?topic=5573090.0))
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [OpenAI Whisper](https://github.com/openai/whisper)

## License

MIT

---

Built by [nytemode](https://nytemode.com)
