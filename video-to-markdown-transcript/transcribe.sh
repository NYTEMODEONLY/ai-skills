#!/usr/bin/env bash
# transcribe.sh - Full video-to-markdown transcript pipeline
#
# Default: Whisper transcription for best quality (punctuated sentences).
# Use --fast to extract existing subtitles instead (instant, no GPU needed).
#
# Usage:
#   ./transcribe.sh "VIDEO_URL" [options]
#
# Options:
#   --lang LANG         Language code (default: en)
#   --output NAME       Output filename without extension (default: transcript)
#   --model MODEL       Whisper model: tiny|base|small|medium|turbo|large (default: turbo)
#   --fast              Use subtitles instead of Whisper (instant but no punctuation)
#
# Examples:
#   ./transcribe.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
#   ./transcribe.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --lang es
#   ./transcribe.sh "https://rumble.com/v123abc" --output "my-notes"
#   ./transcribe.sh "https://www.youtube.com/watch?v=xyz" --model large
#   ./transcribe.sh "https://www.youtube.com/watch?v=xyz" --fast
#
# Requirements:
#   - yt-dlp (required)
#   - ffmpeg (required)
#   - openai-whisper (required unless using --fast)
#
# Install:
#   macOS:  brew install yt-dlp ffmpeg && pip install openai-whisper
#   Linux:  pip install yt-dlp openai-whisper && sudo apt install ffmpeg

set -euo pipefail

# ── Argument Parsing ───────────────────────────────────────────────────────────

URL=""
LANG="en"
OUTPUT="transcript"
WHISPER_MODEL="turbo"
FAST_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang)    LANG="$2"; shift 2 ;;
        --output)  OUTPUT="$2"; shift 2 ;;
        --model)   WHISPER_MODEL="$2"; shift 2 ;;
        --fast)    FAST_MODE=true; shift ;;
        --help|-h)
            head -30 "${BASH_SOURCE[0]}" | grep '^#' | sed 's/^# \?//'
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Run with --help for usage."
            exit 1
            ;;
        *)
            if [ -z "$URL" ]; then
                URL="$1"
            fi
            shift
            ;;
    esac
done

if [ -z "$URL" ]; then
    echo "Usage: transcribe.sh VIDEO_URL [--lang en] [--output name] [--model turbo] [--fast]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="$(mktemp -d)"
SUB_FILE=""

# Cleanup on exit
cleanup() {
    rm -rf "$WORKDIR"
}
trap cleanup EXIT

# ── Dependency Check ───────────────────────────────────────────────────────────

check_deps() {
    if ! command -v yt-dlp &>/dev/null; then
        echo "ERROR: yt-dlp is not installed."
        echo "  macOS:  brew install yt-dlp"
        echo "  Linux:  pip install yt-dlp"
        exit 1
    fi

    if ! command -v ffmpeg &>/dev/null; then
        echo "ERROR: ffmpeg is not installed."
        echo "  macOS:  brew install ffmpeg"
        echo "  Linux:  sudo apt install ffmpeg"
        exit 1
    fi
}

# ── Subtitle Extraction ───────────────────────────────────────────────────────

try_manual_subs() {
    echo "==> Checking for manual (creator-uploaded) subtitles..."
    if yt-dlp --write-subs --sub-langs "$LANG" --convert-subs srt \
        --skip-download -o "$WORKDIR/$OUTPUT" "$URL" 2>/dev/null; then
        SUB_FILE=$(find "$WORKDIR" -name "*.srt" | head -1)
        if [ -n "$SUB_FILE" ] && [ -s "$SUB_FILE" ]; then
            echo "    Found manual subtitles!"
            return 0
        fi
    fi
    SUB_FILE=""
    return 1
}

try_auto_subs() {
    echo "==> Checking for auto-generated subtitles..."
    if yt-dlp --write-auto-subs --sub-langs "$LANG" --convert-subs srt \
        --skip-download -o "$WORKDIR/${OUTPUT}-auto" "$URL" 2>/dev/null; then
        SUB_FILE=$(find "$WORKDIR" -name "*auto*.srt" -o -name "*.srt" | head -1)
        if [ -n "$SUB_FILE" ] && [ -s "$SUB_FILE" ]; then
            echo "    Found auto-generated subtitles!"
            return 0
        fi
    fi
    SUB_FILE=""
    return 1
}

# ── Whisper Transcription ─────────────────────────────────────────────────────

run_whisper() {
    if ! command -v whisper &>/dev/null; then
        echo "ERROR: Whisper is not installed."
        echo "  Install: pip install openai-whisper"
        echo "  Or use --fast to skip Whisper and use subtitles instead."
        exit 1
    fi

    echo "==> Downloading audio..."
    yt-dlp -x --audio-format mp3 --audio-quality 5 \
        -o "$WORKDIR/audio.%(ext)s" "$URL"

    AUDIO_FILE=$(find "$WORKDIR" -name "audio.*" | head -1)
    if [ -z "$AUDIO_FILE" ]; then
        echo "ERROR: Failed to download audio."
        exit 1
    fi

    echo "==> Transcribing with Whisper (model: $WHISPER_MODEL)..."
    echo "    This may take a while depending on video length and model size."
    whisper "$AUDIO_FILE" --model "$WHISPER_MODEL" --output_format srt \
        --output_dir "$WORKDIR" --language "$LANG"

    SUB_FILE=$(find "$WORKDIR" -name "*.srt" | head -1)
    if [ -n "$SUB_FILE" ] && [ -s "$SUB_FILE" ]; then
        echo "    Whisper transcription complete!"
        return 0
    fi

    echo "ERROR: Whisper failed to produce a transcript."
    exit 1
}

# ── Main Pipeline ──────────────────────────────────────────────────────────────

main() {
    check_deps

    echo ""
    echo "Video to Markdown Transcript"
    echo "============================"
    echo "URL:      $URL"
    echo "Language: $LANG"
    echo "Output:   $OUTPUT.md"
    if [ "$FAST_MODE" = true ]; then
        echo "Mode:     Fast (subtitles only)"
    else
        echo "Mode:     Whisper (model: $WHISPER_MODEL)"
    fi
    echo ""

    if [ "$FAST_MODE" = true ]; then
        # --fast: Try subtitles only (manual first, then auto-generated)
        # Falls back to Whisper only if no subtitles exist at all
        try_manual_subs || try_auto_subs || run_whisper
    else
        # Default: Use manual subs if available (they have punctuation),
        # otherwise use Whisper for best quality output
        if ! try_manual_subs; then
            echo "==> No manual subtitles. Using Whisper for best quality..."
            run_whisper
        fi
    fi

    if [ -z "$SUB_FILE" ] || [ ! -s "$SUB_FILE" ]; then
        echo "ERROR: No transcript produced. Check the URL and try again."
        exit 1
    fi

    # Get the video title for the markdown header
    TITLE=$(yt-dlp --get-title "$URL" 2>/dev/null || echo "Video Transcript")

    echo "==> Converting to markdown..."

    # Use the Python converter if available alongside this script
    if [ -f "$SCRIPT_DIR/srt_to_markdown.py" ]; then
        python3 "$SCRIPT_DIR/srt_to_markdown.py" "$SUB_FILE" "$TITLE" \
            --output "$OUTPUT.md" --url "$URL"
    else
        # Inline fallback: basic SRT to markdown conversion
        python3 -c "
import re, sys

with open('$SUB_FILE', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'^WEBVTT\s*\n(?:.*\n)*?\n', '', content, count=1)

blocks = re.split(r'\n\s*\n', content.strip())
lines = []
for block in blocks:
    bl = block.strip().split('\n')
    text_lines = [l for l in bl
                  if not re.match(r'^\d+$', l.strip())
                  and not re.match(r'\d{2}:\d{2}', l.strip())]
    text = ' '.join(text_lines)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{\\\\[^}]+\}', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if text:
        lines.append(text)

# Deduplicate overlapping auto-sub lines
deduped = []
for line in lines:
    if not deduped:
        deduped.append(line)
        continue
    prev = deduped[-1]
    if line == prev:
        continue
    if prev in line:
        deduped[-1] = line
        continue
    if line in prev:
        continue
    pw, cw = prev.split(), line.split()
    merged = False
    for ov in range(min(len(pw), len(cw)), 1, -1):
        if pw[-ov:] == cw[:ov]:
            nw = cw[ov:]
            if nw:
                deduped[-1] = prev + ' ' + ' '.join(nw)
            merged = True
            break
    if not merged:
        deduped.append(line)
lines = deduped

full_text = ' '.join(lines)
full_text = re.sub(r'\s+', ' ', full_text)

# Split into paragraphs by sentence or word count
sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z\[])', full_text)
if len(sentences) > 1:
    paragraphs, current = [], []
    for s in sentences:
        current.append(s)
        if len(current) >= 4:
            paragraphs.append(' '.join(current))
            current = []
    if current:
        paragraphs.append(' '.join(current))
else:
    words = full_text.split()
    paragraphs = []
    for i in range(0, len(words), 100):
        chunk = ' '.join(words[i:i+100])
        if chunk:
            chunk = chunk[0].upper() + chunk[1:]
        paragraphs.append(chunk)

title = '''$TITLE'''
url = '''$URL'''
md = f'# {title}\n\n> Source: {url}\n\n' + '\n\n'.join(paragraphs) + '\n'

with open('$OUTPUT.md', 'w') as f:
    f.write(md)
print(f'Saved: $OUTPUT.md')
"
    fi

    echo ""
    echo "==> Done! Transcript saved to $OUTPUT.md"
    echo ""

    # Show preview
    head -20 "$OUTPUT.md"
    LINES=$(wc -l < "$OUTPUT.md")
    if [ "$LINES" -gt 20 ]; then
        echo "..."
        echo "($LINES total lines)"
    fi
}

main "$@"
