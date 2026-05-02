# AI Skills

A collection of AI agent skills for Claude Code, Codex, OpenClaw, and other AI assistants.

## Skills

| Skill | Description |
|-------|-------------|
| [xai-x-link-reader](./xai-x-link-reader) | Resolve X.com/Twitter links through xAI Grok `x_search` tool calling |
| [video-to-markdown-transcript](./video-to-markdown-transcript) | Transcribe any video into clean, readable markdown using captions-first approach |

## What are Skills?

Skills are reusable knowledge modules that teach AI agents how to accomplish specific tasks. Each skill contains:

- **SKILL.md** - The main skill definition with problem context, solution steps, and verification criteria
- **Supporting files** - Scripts, code, and configuration needed to execute the skill

## Using These Skills

### Codex

Copy a skill folder to your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -r xai-x-link-reader ~/.codex/skills/
```

For API-backed skills, set required environment variables locally. For example:

```bash
export XAI_API_KEY="your_xai_api_key_here"
```

### Claude Code

Copy the skill folder to your Claude Code skills directory:

```bash
cp -r video-to-markdown-transcript ~/.claude/skills/
```

### OpenClaw

Skills are automatically loaded from `~/.openclaw/skills/` or can be synced from ClawHub.

### Manual Usage

Each skill folder contains standalone scripts that can be run directly. Check the README in each skill folder for specific usage instructions.

## Security

Do not commit API keys, `.env` files, private user data, or generated cache files. API-backed skills should read secrets from environment variables.

## Contributing

Feel free to fork and submit PRs with new skills or improvements to existing ones.

## License

MIT

---

Built by [NYTEMODE](https://nytemode.com)
