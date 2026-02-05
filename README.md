# AI Skills

A collection of AI agent skills for Claude Code, OpenClaw, and other AI assistants.

## Skills

| Skill | Description |
|-------|-------------|
| [video-to-markdown-transcript](./video-to-markdown-transcript) | Transcribe any video into clean, readable markdown using captions-first approach |

## What are Skills?

Skills are reusable knowledge modules that teach AI agents how to accomplish specific tasks. Each skill contains:

- **SKILL.md** - The main skill definition with problem context, solution steps, and verification criteria
- **Supporting files** - Scripts, code, and configuration needed to execute the skill

## Using These Skills

### Claude Code

Copy the skill folder to your Claude Code skills directory:

```bash
cp -r video-to-markdown-transcript ~/.claude/skills/
```

### OpenClaw

Skills are automatically loaded from `~/.openclaw/skills/` or can be synced from ClawHub.

### Manual Usage

Each skill folder contains standalone scripts that can be run directly. Check the README in each skill folder for specific usage instructions.

## Contributing

Feel free to fork and submit PRs with new skills or improvements to existing ones.

## License

MIT

---

Built by [NYTEMODE](https://nytemode.com)
