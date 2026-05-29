# App Store Review Audit

A Codex, Claude Code, and OpenClaw skill for auditing Apple platform apps before
App Store Review, TestFlight review, or App Store Connect submission.

The skill produces a repo-grounded readiness verdict, risk register, fix plan,
and reviewer-notes draft. It does not guarantee Apple approval.

## What It Checks

- Build, archive, first-launch, and runtime completeness evidence
- Reviewer access, demo accounts, review notes, and backend availability
- App Store metadata, screenshots, age rating, privacy labels, and support links
- Privacy policy, account deletion, tracking, permissions, SDKs, and data sharing
- In-app purchase, subscriptions, external purchase links, ads, and business model
- User-generated content, moderation, report/block flows, and safety risks
- Entitlements, background modes, notifications, widgets, extensions, and App Clips
- Placeholder content, debug UI, staging endpoints, private API risk, and brand/IP issues

## Quick Start

Run the bundled scanner from this folder:

```bash
python3 scripts/audit_app_store.py /path/to/apple-app --output /tmp/app-store-review-audit.md
```

The scanner is intentionally heuristic. Use it to find leads, then verify each
item manually against the app, the repository, App Store Connect, and current
Apple policy.

## As A Skill

Install for Codex:

```bash
mkdir -p ~/.codex/skills
cp -r app-store-review-audit ~/.codex/skills/
```

Install for Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -r app-store-review-audit ~/.claude/skills/
```

Install for OpenClaw:

```bash
mkdir -p ~/.openclaw/skills
cp -r app-store-review-audit ~/.openclaw/skills/
```

Then ask:

- "Audit this iOS app for App Store Review readiness."
- "Preflight this TestFlight submission and draft reviewer notes."
- "Review this App Review rejection and create a fix plan."
- "Check whether this subscription flow is risky for App Review."

## Recommended Workflow

1. Refresh official Apple sources:
   - <https://developer.apple.com/app-store/review/guidelines/>
   - <https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/overview-of-submitting-for-review>
   - <https://developer.apple.com/help/app-store-connect/manage-app-privacy>
2. Identify the candidate app, platform, version, build, bundle ID, scheme, and
   release configuration.
3. Run `scripts/audit_app_store.py` and review the generated scaffold.
4. Inspect source-of-truth files such as `Info.plist`, `*.entitlements`,
   `PrivacyInfo.xcprivacy`, `project.yml`, `Package.swift`, release docs, privacy
   policy, backend docs, and App Store checklists.
5. Run the repo's documented build, test, archive, or simulator smoke commands.
6. Produce `docs/app-store-review-audit.md` or `APP_STORE_REVIEW_AUDIT.md`.

## Output Artifact

The final audit should include:

- Verdict: `Ready`, `Conditionally ready`, or `Not ready`
- Candidate app, platform, version, build, bundle ID, and audit date
- Policy sources checked with dates
- Evidence commands and source paths
- Blockers, high-risk items, unknowns, manual gates, and fix plan
- Verification matrix and App Store Connect metadata/privacy checklist
- App Review notes draft
- Submit/no-submit recommendation

## Scanner Examples

Write a report:

```bash
python3 scripts/audit_app_store.py ~/Projects/MyApp --output /tmp/myapp-review-audit.md
```

Print to stdout:

```bash
python3 scripts/audit_app_store.py ~/Projects/MyApp
```

Run after installing in Codex:

```bash
python3 ~/.codex/skills/app-store-review-audit/scripts/audit_app_store.py \
  ~/Projects/MyApp \
  --output /tmp/myapp-review-audit.md
```

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Agent-facing trigger conditions and workflow |
| `README.md` | Human-facing documentation |
| `scripts/audit_app_store.py` | Heuristic scanner and Markdown audit scaffold generator |
| `references/apple-review-rubric.md` | Audit rubric, source list, search prompts, and artifact template |
| `agents/openai.yaml` | Codex UI metadata |
| `LICENSE` | MIT license |

## Limitations

- The scanner finds risk signals; it is not a compliance engine.
- Apple policy changes over time, so official sources should be refreshed during
  each audit.
- App Store Connect metadata, privacy nutrition labels, IAP product state, demo
  accounts, and reviewer notes often require manual access.
- Legal, privacy, medical, finance, gambling, kids, and regulated-service claims
  may need qualified review outside the repository.

## License

MIT

---

Built by [NYTEMODE](https://nytemode.com)
