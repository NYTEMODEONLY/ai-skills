# Apple App Review Audit Rubric

Last policy refresh for this rubric: 2026-05-29.

Official sources to refresh during audits:

- App Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- App Store Connect submission help: https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/overview-of-submitting-for-review
- App Store Connect privacy details: https://developer.apple.com/help/app-store-connect/manage-app-privacy
- Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
- Apple Developer Program License Agreement and App Store Connect Help when payments, privacy, or regulated services are in scope.

## Audit Artifact Template

Use this structure for `docs/app-store-review-audit.md` or `APP_STORE_REVIEW_AUDIT.md`:

```markdown
# App Store Review Audit

Verdict: Ready | Conditionally ready | Not ready
Candidate: app name, platform, version, build, bundle ID
Audit date:
Policy sources checked:

## Executive Summary

## Blockers

## High-Risk Review Items

## Unknowns And Manual Gates

## Evidence

## Guideline Risk Matrix

| Area | Status | Evidence | Fix |
| --- | --- | --- | --- |
| Safety |  |  |  |
| Performance |  |  |  |
| Business |  |  |  |
| Design |  |  |  |
| Legal |  |  |  |

## Fix Plan

## Verification Matrix

## App Review Notes Draft

## App Store Connect Metadata Checklist
```

## Submission Gates

Block submission when any of these are true:

- The app crashes, hangs, has broken first launch, or core flows cannot be completed.
- Login is required but reviewers lack an active demo account, full-featured demo mode, or review instructions.
- Backend services, support URLs, privacy URLs, universal links, purchase products, or required assets are not live and reachable.
- App metadata, screenshots, privacy labels, age rating, app name, subtitle, or review notes materially misrepresent the app.
- Placeholder text, debug UI, test data, hidden features, dormant features, or undocumented gated features remain in the release build.
- Digital goods or feature unlocks bypass required in-app purchase without a valid entitlement or region-specific allowance.
- Account creation exists without in-app account deletion or a documented deletion path matching current Apple requirements.
- Privacy policy is missing, inaccessible, inconsistent with actual data collection, or absent from the app UI.
- Permission prompts are vague or request data unrelated to core functionality.
- User-generated content exists without filtering, reporting, blocking, and published contact/support channels.
- Extension, widget, notification, App Clip, or background mode functionality is unrelated to the app or uses unsupported APIs.

## Evidence To Collect

- Candidate version/build and bundle IDs.
- Exact build, test, archive, export, and lint commands run.
- Simulator or device smoke-test notes, including OS/device.
- First launch and account access proof.
- Core workflow proof, including purchases or subscriptions when applicable.
- Privacy policy URL, support URL, terms URL, and in-app locations for these links.
- App Store Connect metadata, screenshots, age rating, privacy labels, review notes, demo account, and export compliance status.
- Entitlements, Info.plist purpose strings, privacy manifest, background modes, associated domains, push settings, and app extension settings.
- Backend/service status for any login, sync, push, purchase, ML, cloud, or content feature required during review.

## Guideline Areas

### Safety

Look for objectionable content, unsafe behavior, medical/physical harm claims, kids category issues, user-generated content, support contact gaps, and data security claims. For UGC or social features, verify filtering, report abuse, block user, moderation response path, and contact information.

Search prompts:

- `rg -n "report|block|moderation|abuse|flag|mute|hide|user generated|ugc|comment|chat|message|post|feed|creator" .`
- `rg -n "medical|diagnos|treat|therapy|fitness|health|emergency|gambling|crypto|cannabis|finance|bank|legal" .`
- `rg -n "support|contact|help|privacy|terms" public docs .`

### Performance

Verify the app is complete, stable, reviewable, and technically compliant. Confirm review access, live backends, no placeholders, no obvious bugs, no private APIs, no unrelated background work, IPv6 readiness for networking apps, and current OS/API behavior. For Mac apps, check sandboxing, packaging, update mechanisms, and no privileged installers.

Search prompts:

- `rg -n "TODO|FIXME|lorem|placeholder|dummy|staging|localhost|127.0.0.1|example.com|debug|test user|coming soon" .`
- `rg -n "UIApplication.shared|performSelector|NSClassFromString|dlopen|dlsym|private API|openURL" .`
- `rg -n "UIBackgroundModes|background|voip|location|bluetooth|audio|fetch|remote-notification" .`
- `find . -name "*Info.plist" -o -name "*.entitlements" -o -name "PrivacyInfo.xcprivacy"`

### Business

Map the business model before judging. Digital content, premium features, subscriptions, virtual currency, tips, NFT-related unlocks, and SaaS access usually require careful in-app purchase review unless a guideline exception or entitlement applies. Physical goods, real-world services, and person-to-person payments have different treatment.

Search prompts:

- `rg -n "StoreKit|Product\\.products|purchase|subscription|subscribe|premium|unlock|paywall|Stripe|PayPal|checkout|price|trial|coupon|credits|tokens|tip" .`
- `rg -n "external purchase|buy on web|manage subscription|billing|license key|promo code|QR code|crypto wallet" .`

Review:

- IAP products are configured, visible, restorable, and reviewable.
- Subscriptions disclose period, price, cancellation, renewal, and ongoing value.
- Review notes explain any non-obvious monetization.
- External purchase links are either not present, United States storefront-specific where permitted, or covered by the appropriate entitlement and regional rules.

### Design

Verify the app has app-like value beyond a website, is not a copycat, avoids spammy metadata, has accurate extension/widget disclosure, and correctly uses Apple services and brands. Third-party brands in app names, icons, keywords, and screenshots need extra scrutiny.

Search prompts:

- `rg -n "webview|WKWebView|SFSafariViewController|iframe|link list|directory|catalog" .`
- `rg -n "Apple Music|MusicKit|Sign in with Apple|Apple Pay|Wallet|Spotify|YouTube|Google|Facebook|X|Twitter|TikTok" .`
- `find . -iname "*widget*" -o -iname "*extension*" -o -iname "*appclip*"`

Review:

- App name, icon, keywords, and screenshots do not misuse another developer's brand.
- Sign in with Apple or an equivalent privacy-preserving login is offered when required by third-party/social login usage.
- Widgets, extensions, App Clips, notifications, and background features are related to the app's core functionality and disclosed where needed.
- Apple Music, Push Notifications, Game Center, Apple Pay, Wallet, and other Apple services follow service-specific restrictions.

### Legal And Privacy

Privacy is often the highest-risk area. Compare actual data collection, SDKs, analytics, tracking, permissions, account deletion, retention, and third-party sharing against the privacy policy, in-app disclosures, and App Store privacy labels.

Search prompts:

- `rg -n "Analytics|Firebase|Amplitude|Segment|Mixpanel|Sentry|Crashlytics|AdMob|AppsFlyer|Adjust|tracking|IDFA|ATT|NSUserTrackingUsageDescription" .`
- `rg -n "delete account|account deletion|erase|remove account|deactivate|export data|privacy|retention|consent|opt out|marketing" .`
- `rg -n "NS[A-Za-z]+UsageDescription|CLLocation|AVCapture|PHPhotoLibrary|Contacts|CNContact|HealthKit|HKHealthStore|Bluetooth|Microphone|Camera" .`

Review:

- Privacy policy is accessible in App Store Connect metadata and inside the app.
- Policy states collected data, uses, sharing, third-party protections, retention/deletion, and consent withdrawal.
- Purpose strings are specific and match actual permission use.
- Data collection is minimized and not required unless core to the app.
- Account deletion is available in app when account creation is supported.
- Third-party AI or data processors are disclosed where personal data is shared.
- Tracking uses App Tracking Transparency when required and is not forced for access.
- Regulated services are submitted by the appropriate legal entity and include required disclosures, licenses, or geo-restrictions.

## Reviewer Notes Checklist

Draft notes should include:

- Demo account credentials or demo mode instructions.
- Backend availability and any required region, device, OS, entitlement, hardware, QR code, invite code, seed data, or test account setup.
- Non-obvious flows and where to find them.
- In-app purchases, subscriptions, trial behavior, restore path, and sandbox setup.
- Login, account deletion, privacy controls, notification opt-in/out, and support contact locations.
- Explanation of any extension, widget, App Clip, background mode, push payload, associated domain, HealthKit, MusicKit, Apple Pay, Wallet, or other entitlement.
- Known limitations that are intentional and compliant, without describing bugs as features.

## Fix Plan Standards

For each fix, include:

- Severity: blocker, high, medium, low.
- Guideline area and likely guideline number when known.
- Files or App Store Connect fields to change.
- Exact implementation plan.
- Verification command or manual test.
- Owner if work is outside the repo, such as App Store Connect metadata or legal review.
