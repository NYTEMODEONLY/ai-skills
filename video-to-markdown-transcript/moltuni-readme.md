# Video to Markdown Transcript

Transcribe any video into clean, readable markdown. Inspired by Ditto's "captions-first" philosophy.

## How It Works

1. **Default mode**: Extracts manual subtitles if available, otherwise uses Whisper AI for best quality (punctuated sentences)
2. **Fast mode** (`--fast`): Extracts existing subtitles only (instant, no GPU needed)

## Usage

```bash
# Basic usage
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID"

# Spanish transcript
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --lang es

# Fast mode (subtitles only)
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --fast

# Use larger Whisper model
./transcribe.sh "https://www.youtube.com/watch?v=VIDEO_ID" --model large
```

## Supported Platforms

- YouTube, Rumble, Vimeo (instant subtitles)
- Coursera, Udemy, Teachable (may need auth cookies)
- Local video/audio files (Whisper transcription)

## References

- [Ditto Transcript Generator](https://dittotranscriptgenerator.com)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [OpenAI Whisper](https://github.com/openai/whisper)

Built by [NYTEMODE](https://nytemode.com)
