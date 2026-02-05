---
name: video-to-markdown-transcript
description: |
  Transcribe any video (YouTube, Rumble, Udemy, Coursera, local files, or any URL) into clean
  markdown text. Inspired by Ditto's "captions-first" philosophy: extract existing subtitles
  before falling back to AI transcription. Use when: (1) user wants to transcribe a video to
  text/markdown, (2) user wants lecture notes from a video, (3) user wants a readable transcript
  without timestamps, (4) user has a video URL or local video/audio file to convert to text,
  (5) user says "transcribe this video" or "get the transcript", (6) user wants to convert
  subtitles/captions to clean readable text, (7) user wants to create markdown notes from
  video content. Covers yt-dlp subtitle extraction, Whisper local transcription, SRT/VTT
  parsing, and markdown formatting.
author: NYTEMODE
version: 1.0.0
date: 2026-02-04
---

# Video to Markdown Transcript

## Problem

You need to convert a video (from a URL or local file) into clean, readable markdown text.
Most transcription workflows produce messy output with timestamps, fragmented lines, and
poor paragraph structure. This skill implements the "Ditto approach" -- prioritize extracting
existing captions/subtitles (which are already on the platform) before falling back to
AI-powered speech recognition via Whisper.

## Context / Trigger Conditions

- User provides a video URL (YouTube, Rumble, Vimeo, Coursera, Udemy, etc.) and wants a transcript
- User has a local video or audio file they want transcribed
- User says "transcribe this video", "get the transcript", "convert this to text"
- User wants lecture notes, study material, or readable text from video content
- User wants clean markdown without timestamps or subtitle formatting artifacts

## Prerequisites

### Required Tools
- **yt-dlp**: For downloading subtitles and audio from URLs
- **ffmpeg**: For audio extraction and format conversion (required by both yt-dlp and Whisper)

### Optional Tools (for fallback transcription)
- **whisper** (OpenAI): For local AI transcription when no subtitles exist

### Installation (macOS)
```bash
brew install yt-dlp ffmpeg
pip install openai-whisper
```

### Installation (Linux)
```bash
pip install yt-dlp openai-whisper
sudo apt install ffmpeg   # Debian/Ubuntu
```

## Solution

### Strategy: Captions-First (The Ditto Approach)

**Always try to extract existing subtitles first.** Platform-generated or creator-uploaded
captions are faster to obtain, require no GPU, and are often higher quality than
re-transcribing audio. Only fall back to Whisper when no subtitles are available.

---

### Step 1: Check for Available Subtitles

List all available subtitle tracks for a video URL:

```bash
yt-dlp --list-subs "VIDEO_URL"
```

This shows both manual (creator-uploaded) and auto-generated subtitle tracks with their
language codes.

### Step 2a: Extract Existing Subtitles (Preferred Path)

Download subtitles without downloading the video. Prefer manual subs over auto-generated:

```bash
# Try manual subtitles first (higher quality)
yt-dlp --write-subs --sub-langs "en" --sub-format srt --convert-subs srt \
  --skip-download -o "transcript" "VIDEO_URL"

# If no manual subs, try auto-generated
yt-dlp --write-auto-subs --sub-langs "en" --sub-format srt --convert-subs srt \
  --skip-download -o "transcript" "VIDEO_URL"
```

This produces a file like `transcript.en.srt`.

#### For other languages, change the language code:
```bash
# Spanish subtitles
yt-dlp --write-subs --write-auto-subs --sub-langs "es" --convert-subs srt \
  --skip-download -o "transcript" "VIDEO_URL"

# Multiple languages
yt-dlp --write-subs --write-auto-subs --sub-langs "en,es,fr" --convert-subs srt \
  --skip-download -o "transcript" "VIDEO_URL"
```

### Step 2b: Whisper Transcription (Fallback Path)

When no subtitles are available, download audio and transcribe locally with Whisper:

```bash
# Download audio only (smallest file)
yt-dlp -x --audio-format mp3 --audio-quality 5 -o "audio.%(ext)s" "VIDEO_URL"

# Transcribe with Whisper
whisper audio.mp3 --model turbo --output_format srt --language en
```

#### Whisper Model Selection
| Model   | Size   | Speed      | Quality    | Use When                      |
|---------|--------|------------|------------|-------------------------------|
| tiny    | 39M    | ~32x       | Basic      | Quick draft, checking content |
| base    | 74M    | ~16x       | Good       | Short videos, clear audio     |
| small   | 244M   | ~6x        | Better     | General use                   |
| medium  | 769M   | ~2x        | Great      | Important content             |
| turbo   | 809M   | ~8x        | Great      | Best speed/quality tradeoff   |
| large   | 1550M  | ~1x        | Best       | Critical accuracy needed      |

For local files, skip the download step:
```bash
whisper /path/to/video.mp4 --model turbo --output_format srt --language en
```

### Step 3: Convert SRT/VTT to Clean Markdown

Use the included `srt_to_markdown.py` script:

```bash
python3 srt_to_markdown.py transcript.en.srt "Video Title Here"
```

Or use the full pipeline script:

```bash
./transcribe.sh "VIDEO_URL"
```

### Step 4: Inline Usage (Without Scripts)

When executing directly in a Claude Code or OpenClaw session, run commands
sequentially without saving scripts:

```bash
# 1. Set variables
VIDEO_URL="https://www.youtube.com/watch?v=XXXXX"
WORK_DIR=$(mktemp -d)
LANG="en"

# 2. Try subtitles first
yt-dlp --write-subs --write-auto-subs --sub-langs "$LANG" \
  --convert-subs srt --skip-download -o "$WORK_DIR/video" "$VIDEO_URL"

# 3. Check what we got
SUB_FILE=$(ls "$WORK_DIR"/*.srt 2>/dev/null | head -1)

# 4. If no subs, use Whisper
if [ -z "$SUB_FILE" ]; then
  yt-dlp -x --audio-format mp3 --audio-quality 5 -o "$WORK_DIR/audio.%(ext)s" "$VIDEO_URL"
  whisper "$WORK_DIR/audio.mp3" --model turbo --output_format srt \
    --output_dir "$WORK_DIR" --language "$LANG"
  SUB_FILE="$WORK_DIR/audio.srt"
fi

# 5. Convert to markdown
python3 srt_to_markdown.py "$SUB_FILE" "$(yt-dlp --get-title "$VIDEO_URL")"
```

## Verification

1. Output markdown file exists and is non-empty
2. No timestamp artifacts (e.g., `00:01:23,456 --> 00:01:25,789`) in output
3. No subtitle index numbers (bare `1`, `2`, `3` on lines) in output
4. Text flows in natural paragraphs, not one-line-per-caption fragments
5. HTML tags (`<i>`, `<b>`, etc.) are stripped
6. Bracket notes like `[Music]` or `[Applause]` are preserved but not duplicated

## Example

**Scenario**: User provides a YouTube URL and asks for a readable transcript.

**Raw SRT (before)**:
```
1
00:00:00,000 --> 00:00:03,500
Welcome to this presentation about

2
00:00:03,500 --> 00:00:06,200
Bitcoin mining and how it works.

3
00:00:06,500 --> 00:00:10,800
Today we're going to cover three main topics.
```

**Clean Markdown (after)**:
```markdown
# Bitcoin Mining Explained

Welcome to this presentation about Bitcoin mining and how it works. Today we're going
to cover three main topics.
```

## Platform-Specific Notes

### YouTube
- Almost always has auto-generated subtitles in English
- Manual subs (when available) are significantly better quality
- yt-dlp handles YouTube natively with no extra config

### Rumble
- yt-dlp supports Rumble URLs
- Fewer videos have subtitles; Whisper fallback is more common

### Coursera / Udemy / Teachable / Kajabi
- Course platforms usually have high-quality manual subtitles
- May require authentication cookies for yt-dlp:
  ```bash
  yt-dlp --cookies-from-browser chrome --write-subs --skip-download "URL"
  ```

### Local Files
- Skip yt-dlp entirely. Feed the file directly to Whisper:
  ```bash
  whisper video.mp4 --model turbo --output_format srt --language en
  ```
- Then convert the resulting SRT to markdown

## Notes

- **Captions-first is faster**: Subtitle extraction completes in seconds vs minutes for Whisper
- **No GPU needed for subs**: Whisper benefits from GPU but subtitle extraction does not
- **Privacy**: Like Ditto, subtitle extraction is fully local -- no data leaves your machine
- **Whisper is also local**: OpenAI Whisper runs entirely on your machine, no API calls
- **Language support**: Both yt-dlp and Whisper support dozens of languages
- **Large videos**: For very long videos (2+ hours), Whisper may need significant RAM/time;
  subtitle extraction remains fast regardless of length
- **Auto-sub quality**: YouTube's auto-generated subtitles have improved dramatically but
  still struggle with technical jargon, proper nouns, and heavy accents
- When NOT to use this skill: If the user already has a text transcript and just needs formatting

## References

- [Ditto Transcript Generator](https://dittotranscriptgenerator.com) -- the inspiration for the captions-first approach
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [BitcoinTalk Ditto Thread](https://bitcointalk.org/index.php?topic=5573090.0)
