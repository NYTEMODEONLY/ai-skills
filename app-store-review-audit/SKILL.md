---
name: app-store-review-audit
description: |
  Audit and prepare Apple platform apps for App Store Review, TestFlight review,
  or App Store Connect submission. Use when Codex is asked to review, preflight,
  submit, launch, prepare metadata for, reduce rejection risk for, or respond to
  rejection feedback for iOS, iPadOS, macOS, watchOS, tvOS, visionOS, WidgetKit,
  extension, App Clip, in-app purchase, or App Store Connect submissions.
author: NYTEMODE
version: 1.0.0
date: 2026-05-29
---

# App Store Review Audit

## Problem

Apple platform apps can fail App Review for issues that are easy to miss in a
normal code review: missing reviewer access, inaccurate metadata, broken privacy
links, incomplete account deletion, non-compliant payments, placeholder release
content, entitlement misuse, or unverified backend dependencies.

This skill turns a local app repository into a concrete App Review readiness
verdict, risk register, and fix plan. It lowers rejection risk without claiming
Apple approval is guaranteed.

## Context / Trigger Conditions

Use this skill when the user asks to:

- Audit or preflight an iOS, iPadOS, macOS, watchOS, tvOS, or visionOS app before
  App Review, TestFlight review, or App Store Connect submission.
- Prepare launch, release, review notes, App Store metadata, privacy details, or
  reviewer demo access.
- Reduce App Review rejection risk for in-app purchases, subscriptions, privacy,
  tracking, account deletion, user-generated content, notifications, widgets,
  extensions, App Clips, or entitlement use.
- Respond to App Review rejection feedback with a repo-grounded fix plan.

## Prerequisites

- Local access to the app source, release branch, or candidate build artifacts.
- `python3` for the bundled heuristic scanner.
- Network access when available so official Apple policy pages can be refreshed
  before making current compliance claims.
- Xcode command line tools for Apple native build checks when the project uses
  Xcode, Swift Package Manager, XcodeGen, CocoaPods, or archive/export scripts.
- App Store Connect access, demo credentials, device access, payment sandbox, or
  backend/operator access when those items are necessary. If unavailable, mark
  them as manual gates instead of assuming they pass.

## Solution Steps

### 1. Refresh Policy Context

Treat Apple App Review guidance as live policy. When network access is available,
refresh the official sources before making current compliance claims:

- App Review Guidelines: <https://developer.apple.com/app-store/review/guidelines/>
- Submission overview: <https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/overview-of-submitting-for-review>
- App privacy details: <https://developer.apple.com/help/app-store-connect/manage-app-privacy>
- Human Interface Guidelines: <https://developer.apple.com/design/human-interface-guidelines/>

Use `references/apple-review-rubric.md` for the local audit rubric, source list,
search prompts, artifact template, and submission gates.

### 2. Build A Project Map

Identify the candidate app and scope before concluding readiness:

- Platform, app target, scheme, version, build number, bundle ID, and release
  configuration.
- Extensions, widgets, App Clips, watch apps, notification services, background
  modes, associated domains, and entitlements.
- Login model, reviewer access, demo account, demo mode, invite codes, test data,
  and account deletion.
- Backend dependencies, push notifications, cloud sync, AI services, analytics,
  support URL, privacy policy URL, terms URL, and service status.
- Payments, in-app purchase products, subscriptions, external purchase links,
  ads, virtual goods, credits, tips, or other monetization.
- User-generated content, social features, moderation, report/block flows, and
  support contacts.
- Third-party SDKs, tracking, permission prompts, privacy manifest, data sharing,
  and App Store privacy-label implications.

Prefer source-of-truth config and docs such as `project.yml`, `Package.swift`,
`*.xcodeproj/project.pbxproj`, `*.xcworkspace`, `Info.plist`, `*.entitlements`,
`PrivacyInfo.xcprivacy`, `firebase.json`, app config, release notes, privacy
policy, launch checklist, and backend docs.

### 3. Run The Scanner

Run the bundled scanner as a first-pass aid. Resolve the script relative to the
installed skill folder:

```bash
python3 scripts/audit_app_store.py /path/to/app --output /tmp/app-store-review-audit.md
```

If the skill is installed in Codex:

```bash
python3 ~/.codex/skills/app-store-review-audit/scripts/audit_app_store.py \
  /path/to/app \
  --output /tmp/app-store-review-audit.md
```

The scanner is heuristic. Use its findings to guide manual inspection, not as
final truth.

### 4. Verify Build And Runtime Evidence

- Use the repository's own preflight, lint, test, build, archive, and export
  commands first.
- For Xcode projects, prefer non-destructive commands such as `xcodebuild -list`,
  `xcodebuild -showBuildSettings`, and documented archive/export scripts.
- If simulator or device testing is feasible, smoke-test first launch, auth/demo
  access, core flows, settings, support/privacy links, purchase/subscription
  surfaces, notification permission flows, account deletion, and every extension,
  widget, or App Clip in scope.
- If real-device, backend, payment sandbox, App Store Connect, or operator access
  is required and unavailable, mark the item as unverified.

### 5. Review Apple Risk Areas

- Safety: objectionable content, user-generated content moderation, kids,
  physical harm, medical/health, support contact, and data security.
- Performance: app completeness, crashes, placeholders, reviewer access,
  metadata accuracy, hardware compatibility, public APIs, background modes, IPv6,
  extensions, widgets, and notifications.
- Business: in-app purchase, subscriptions, external purchase links, Apple Pay,
  ads, paid digital goods, virtual currency, and non-obvious business models.
- Design: minimum functionality, copycats, brand misuse, spam, Apple service use,
  Sign in with Apple parity, widgets, extensions, and app-like value.
- Legal: privacy policy, consent, data minimization, account deletion, tracking,
  third-party SDKs/data sharing, regulated services, IP rights, age rating, and
  export compliance.

### 6. Produce The Review Artifact

Default location:

- `docs/app-store-review-audit.md` if the repo has `docs/`
- `APP_STORE_REVIEW_AUDIT.md` otherwise

Include:

- Verdict: `Ready`, `Conditionally ready`, or `Not ready`
- Candidate app, platform, version, build, bundle ID, and audit date
- Policy sources checked with dates
- Evidence commands and source paths
- Blockers, high-risk items, unknowns, manual gates, and fix plan
- Verification matrix and App Store Connect metadata/privacy checklist
- App Review notes draft
- Submit/no-submit recommendation

If the user asks for fixes, implement scoped fixes after the audit and update the
artifact with verification evidence.

## Verification Criteria

An audit is complete only when:

1. The final report starts with `Ready`, `Conditionally ready`, or `Not ready`.
2. Every blocker and high-risk item cites evidence: file path, command output,
   route, screenshot, App Store Connect field, runtime test, or Apple guideline
   area.
3. Unknowns are listed as manual gates instead of hidden in prose.
4. Build, test, archive, simulator, device, backend, payment, and App Store
   Connect checks are marked as verified or unavailable.
5. Reviewer notes explain demo access, non-obvious flows, entitlement use,
   purchases/subscriptions, backend dependencies, test data, and account deletion
   where applicable.
6. The report avoids legal certainty. Use phrases such as "likely risk", "needs
   legal/privacy review", or "Apple may reject" when policy interpretation is
   required.

## Readiness Labels

- `Ready`: no known blockers; key flows, metadata, privacy, reviewer access, and
  build/archive evidence are verified for the candidate.
- `Conditionally ready`: likely submit-capable after explicitly listed manual
  checks, App Store Connect-only items, or real-device tests.
- `Not ready`: one or more likely rejection blockers, missing reviewer access,
  broken core flows, missing privacy/support metadata, non-compliant payments,
  crashes, placeholders, or unverified required infrastructure.

## Examples

### Preflight A Local iOS App

```bash
python3 ~/.codex/skills/app-store-review-audit/scripts/audit_app_store.py \
  /Users/me/projects/MyApp \
  --output /tmp/myapp-app-store-review-audit.md
```

Then inspect the app manually, refresh official Apple policy pages, run the
project's build/test commands, and write `docs/app-store-review-audit.md` with a
readiness verdict and fix plan.

### Respond To Rejection Feedback

If the user provides App Review rejection text, map each issue to:

- Apple guideline area and likely guideline number when known
- Evidence in the repo, runtime app, metadata, or App Store Connect
- Concrete fix
- Verification command or manual retest
- Draft response to Apple in plain language
