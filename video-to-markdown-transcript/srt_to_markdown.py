#!/usr/bin/env python3
"""
srt_to_markdown.py - Convert SRT/VTT subtitle files to clean markdown transcripts.

Strips timestamps, merges fragmented caption lines into natural paragraphs,
removes HTML tags and positioning artifacts, and outputs readable markdown.

Uses timestamp gaps to detect natural speech pauses for paragraph breaks,
with word-count limits as a safety net for unpunctuated auto-generated subs.

Inspired by Ditto Transcript Generator's clean-formatting philosophy.

Usage:
    python3 srt_to_markdown.py <subtitle_file> [title] [--output FILE]

Examples:
    python3 srt_to_markdown.py video.en.srt
    python3 srt_to_markdown.py video.en.srt "My Video Title"
    python3 srt_to_markdown.py lecture.vtt "Lecture 1" --output notes.md
    python3 srt_to_markdown.py video.en.srt --timestamps
"""

import argparse
import os
import re
import sys


# ── Timestamp Parsing ──────────────────────────────────────────────────────────


def ts_to_seconds(ts: str) -> float:
    """Convert SRT/VTT timestamp string to seconds.

    Handles both comma (SRT: 00:01:23,456) and dot (VTT: 00:01:23.456) formats.
    """
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return 0.0


def seconds_to_mmss(seconds: float) -> str:
    """Convert seconds to MM:SS display format."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


# ── Text Cleaning ─────────────────────────────────────────────────────────────


def clean_subtitle_text(text: str) -> str:
    """Remove HTML tags, positioning codes, and other subtitle artifacts."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{\\[^}]+\}", "", text)
    text = re.sub(r"\s*align:\w+\s*position:\d+%.*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ── SRT/VTT Parsing with Timestamps ───────────────────────────────────────────


def parse_srt_timed(content: str) -> list[tuple[float, float, str]]:
    """Parse SRT content into (start_seconds, end_seconds, text) tuples."""
    blocks = re.split(r"\n\s*\n", content.strip())
    entries: list[tuple[float, float, str]] = []

    for block in blocks:
        block_lines = block.strip().split("\n")
        if len(block_lines) < 3:
            continue

        ts_match = re.match(
            r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})",
            block_lines[1],
        )
        if not ts_match:
            continue

        start = ts_to_seconds(ts_match.group(1))
        end = ts_to_seconds(ts_match.group(2))
        text = " ".join(block_lines[2:])
        text = clean_subtitle_text(text)
        if text:
            entries.append((start, end, text))

    return entries


def parse_vtt_timed(content: str) -> list[tuple[float, float, str]]:
    """Parse VTT content into (start_seconds, end_seconds, text) tuples."""
    # Remove VTT header
    content = re.sub(r"^WEBVTT[^\n]*\n(?:.*\n)*?\n", "", content, count=1)

    entries: list[tuple[float, float, str]] = []
    blocks = re.split(r"\n\s*\n", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")

        # Find the timestamp line
        ts_line = None
        text_lines = []
        for line in lines:
            ts_match = re.match(
                r"(\d{2}:\d{2}[:\.][\d:.]+)\s*-->\s*(\d{2}:\d{2}[:\.][\d:.]+)",
                line,
            )
            if ts_match:
                ts_line = ts_match
            elif ts_line is not None:
                # Lines after timestamp are text
                cleaned = clean_subtitle_text(line)
                if cleaned and not re.match(r"^\d+$", cleaned):
                    text_lines.append(cleaned)

        if ts_line and text_lines:
            start = ts_to_seconds(ts_line.group(1))
            end = ts_to_seconds(ts_line.group(2))
            text = " ".join(text_lines)
            entries.append((start, end, text))

    return entries


# ── Deduplication ──────────────────────────────────────────────────────────────


def deduplicate_timed(
    entries: list[tuple[float, float, str]],
) -> list[tuple[float, float, str]]:
    """Remove duplicate/overlapping entries from auto-generated subtitles.

    YouTube auto-generated VTT subtitles use rolling cues where each segment
    overlaps with the next. This produces 2-3 copies of every phrase.
    Keeps the earliest start time and latest end time for merged entries.
    """
    if not entries:
        return entries

    deduped: list[tuple[float, float, str]] = []

    for start, end, text in entries:
        if not deduped:
            deduped.append((start, end, text))
            continue

        prev_start, prev_end, prev_text = deduped[-1]

        # Skip exact text duplicates
        if text == prev_text:
            deduped[-1] = (prev_start, max(prev_end, end), prev_text)
            continue

        # Previous is substring of current (progressive buildup) -> replace
        if prev_text in text:
            deduped[-1] = (prev_start, max(prev_end, end), text)
            continue

        # Current is substring of previous -> skip
        if text in prev_text:
            deduped[-1] = (prev_start, max(prev_end, end), prev_text)
            continue

        # Check for word-level partial overlap
        prev_words = prev_text.split()
        curr_words = text.split()
        max_overlap = min(len(prev_words), len(curr_words))
        overlap_found = False

        for overlap_size in range(max_overlap, 1, -1):
            if prev_words[-overlap_size:] == curr_words[:overlap_size]:
                new_words = curr_words[overlap_size:]
                if new_words:
                    merged = prev_text + " " + " ".join(new_words)
                    deduped[-1] = (prev_start, max(prev_end, end), merged)
                else:
                    deduped[-1] = (prev_start, max(prev_end, end), prev_text)
                overlap_found = True
                break

        if not overlap_found:
            deduped.append((start, end, text))

    return deduped


# ── Paragraph Building ─────────────────────────────────────────────────────────


# Gap threshold in seconds: pauses longer than this suggest a paragraph break
GAP_THRESHOLD = 1.5
# Maximum words per paragraph before forcing a break
MAX_WORDS_PER_PARA = 100
# Minimum words per paragraph to avoid tiny fragments
MIN_WORDS_PER_PARA = 30


def build_paragraphs(
    entries: list[tuple[float, float, str]],
    gap_threshold: float = GAP_THRESHOLD,
    max_words: int = MAX_WORDS_PER_PARA,
    min_words: int = MIN_WORDS_PER_PARA,
    include_timestamps: bool = False,
) -> list[str]:
    """Build paragraphs from timed subtitle entries.

    Uses three signals for paragraph breaks (in priority order):
    1. Punctuation: sentence-ending punctuation (.!?) followed by a capital letter
    2. Timestamp gaps: silence gaps > gap_threshold seconds between cues
    3. Word count: force a break after max_words to prevent wall-of-text

    Also capitalizes the first letter of each paragraph.
    """
    if not entries:
        return []

    entries = deduplicate_timed(entries)

    paragraphs: list[str] = []
    current_words: list[str] = []
    current_start: float = entries[0][0]
    word_count = 0

    for i, (start, end, text) in enumerate(entries):
        words = text.split()
        if not words:
            continue

        # Check if there's a significant gap before this entry
        if i > 0:
            prev_end = entries[i - 1][1]
            gap = start - prev_end

            # Gap-based paragraph break (only if we have enough words already)
            if gap >= gap_threshold and word_count >= min_words:
                para = _finalize_paragraph(
                    current_words, current_start, include_timestamps
                )
                if para:
                    paragraphs.append(para)
                current_words = []
                word_count = 0
                current_start = start

        current_words.extend(words)
        word_count += len(words)

        # Word-count-based paragraph break: keep splitting until under limit
        while word_count >= max_words:
            # Try to break at a sentence boundary near max_words
            break_idx = _find_sentence_break(current_words, max_words)
            if break_idx > 0:
                para = _finalize_paragraph(
                    current_words[:break_idx], current_start, include_timestamps
                )
                if para:
                    paragraphs.append(para)
                current_words = current_words[break_idx:]
                word_count = len(current_words)
                current_start = start
            else:
                # No sentence break: split at max_words exactly
                para = _finalize_paragraph(
                    current_words[:max_words], current_start, include_timestamps
                )
                if para:
                    paragraphs.append(para)
                current_words = current_words[max_words:]
                word_count = len(current_words)
                current_start = start

    # Flush remaining words
    if current_words:
        para = _finalize_paragraph(
            current_words, current_start, include_timestamps
        )
        if para:
            paragraphs.append(para)

    # If we still ended up with very few paragraphs (all one block),
    # do a final pass splitting on punctuation or word count
    if len(paragraphs) <= 1 and paragraphs:
        paragraphs = _split_long_paragraphs(paragraphs[0], max_words)

    return paragraphs


def _find_sentence_break(words: list[str], target: int) -> int:
    """Find a sentence-ending position near the target word count.

    Looks for words ending in .!? in the range [target-30, target+10].
    Returns the index AFTER the sentence-ending word, or 0 if not found.
    """
    search_start = max(0, target - 30)
    search_end = min(len(words), target + 10)

    # Search backwards from target for best break point
    for idx in range(min(search_end, len(words)) - 1, search_start - 1, -1):
        if words[idx].rstrip('"\'').endswith((".", "!", "?")):
            return idx + 1
    return 0


def _finalize_paragraph(
    words: list[str], start_time: float, include_timestamps: bool
) -> str:
    """Join words into a paragraph, capitalize first letter, optionally add timestamp."""
    if not words:
        return ""
    text = " ".join(words)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    # Capitalize first letter
    text = text[0].upper() + text[1:]

    if include_timestamps:
        ts = seconds_to_mmss(start_time)
        return f"**[{ts}]** {text}"
    return text


def _split_long_paragraphs(text: str, max_words: int) -> list[str]:
    """Last-resort splitting for a single long paragraph.

    Tries sentence boundaries first, falls back to word-count splitting.
    """
    # Try splitting on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\[])", text)
    if len(sentences) > 1:
        # Group into paragraphs of ~3-4 sentences
        paragraphs = []
        current: list[str] = []
        for s in sentences:
            current.append(s)
            if len(current) >= 4:
                paragraphs.append(" ".join(current))
                current = []
        if current:
            paragraphs.append(" ".join(current))
        return paragraphs

    # No punctuation at all: split by word count
    words = text.split()
    paragraphs = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        # Capitalize first letter
        if chunk:
            chunk = chunk[0].upper() + chunk[1:]
        paragraphs.append(chunk)
    return paragraphs


# ── Markdown Assembly ──────────────────────────────────────────────────────────


def to_markdown(
    paragraphs: list[str],
    title: str | None = None,
    source_url: str | None = None,
) -> str:
    """Build final markdown document from paragraphs."""
    md_lines: list[str] = []

    if title:
        md_lines.append(f"# {title}")
        md_lines.append("")

    if source_url:
        md_lines.append(f"> Source: {source_url}")
        md_lines.append("")

    for para in paragraphs:
        md_lines.append(para)
        md_lines.append("")

    return "\n".join(md_lines).strip() + "\n"


# ── Public API ─────────────────────────────────────────────────────────────────


def convert_file(
    input_path: str,
    title: str | None = None,
    output_path: str | None = None,
    source_url: str | None = None,
    include_timestamps: bool = False,
    max_words: int = MAX_WORDS_PER_PARA,
    gap_threshold: float = GAP_THRESHOLD,
) -> str:
    """Convert a subtitle file to markdown. Returns the markdown string."""
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".vtt":
        entries = parse_vtt_timed(content)
    else:
        entries = parse_srt_timed(content)

    paragraphs = build_paragraphs(
        entries,
        gap_threshold=gap_threshold,
        max_words=max_words,
        include_timestamps=include_timestamps,
    )

    markdown = to_markdown(paragraphs, title=title, source_url=source_url)

    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return markdown


# ── CLI ────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Convert SRT/VTT subtitle files to clean markdown transcripts."
    )
    parser.add_argument("input", help="Path to SRT or VTT subtitle file")
    parser.add_argument(
        "title", nargs="?", default=None, help="Title for the markdown document"
    )
    parser.add_argument(
        "--output", "-o", default=None, help="Output markdown file path"
    )
    parser.add_argument(
        "--url", default=None, help="Source video URL to include in output"
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Include periodic timestamp markers in output",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=MAX_WORDS_PER_PARA,
        help=f"Max words per paragraph (default: {MAX_WORDS_PER_PARA})",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=GAP_THRESHOLD,
        help=f"Silence gap in seconds to trigger paragraph break (default: {GAP_THRESHOLD})",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    markdown = convert_file(
        input_path=args.input,
        title=args.title,
        output_path=args.output,
        source_url=args.url,
        include_timestamps=args.timestamps,
        max_words=args.max_words,
        gap_threshold=args.gap,
    )

    out_path = args.output or os.path.splitext(args.input)[0] + ".md"
    print(f"Transcript saved to: {out_path}")

    preview = markdown[:500]
    if len(markdown) > 500:
        preview += "..."
    print(preview)


if __name__ == "__main__":
    main()
