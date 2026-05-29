#!/usr/bin/env python3
"""Heuristic App Store review audit scaffold generator.

This script scans a local Apple app project for common App Review risk signals
and writes a Markdown report scaffold. It is intentionally conservative: every
finding needs human/agent verification against the current Apple guidelines.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import plistlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".svn",
    ".hg",
    ".build",
    ".swiftpm",
    ".deriveddata",
    "DerivedData",
    "build",
    "Build",
    "dist",
    "node_modules",
    "Pods",
    ".next",
    ".vercel",
    ".expo",
    "xcuserdata",
    "Package.resolved",
}
SKIP_DIRS_LOWER = {name.lower() for name in SKIP_DIRS}
DOC_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "README.md", "CHANGELOG.md", "LICENSE.md"}
DOC_DIR_NAMES = {"docs", "documentation", "feedback", "notes", "handoff"}

TEXT_EXTS = {
    ".swift",
    ".m",
    ".mm",
    ".h",
    ".plist",
    ".entitlements",
    ".xcconfig",
    ".pbxproj",
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".txt",
    ".html",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".dart",
    ".kt",
    ".java",
    ".xml",
    ".xcprivacy",
}

MAX_TEXT_FILE_BYTES = 1_000_000

PATTERNS = {
    "placeholder_release_content": re.compile(
        r"\b(TODO|FIXME|XXX|lorem ipsum|placeholder|dummy data|coming soon|example\.com|localhost|127\.0\.0\.1)\b",
        re.IGNORECASE,
    ),
    "login_or_auth": re.compile(
        r"\b(Sign in|SignIn|Login|Log in|Auth|Authentication|FirebaseAuth|OAuth|demo account|account creation)\b",
        re.IGNORECASE,
    ),
    "account_deletion": re.compile(
        r"\b(delete account|account deletion|remove account|deactivate account|erase account|close account)\b",
        re.IGNORECASE,
    ),
    "privacy_support_terms": re.compile(
        r"\b(privacy policy|privacy|terms|support|contact us|help center)\b",
        re.IGNORECASE,
    ),
    "payments": re.compile(
        r"\b(StoreKit|In-App Purchase|IAP|subscription|subscribe|paywall|premium|feature unlock|Stripe|PayPal|checkout|billing|trial|price|purchase)\b",
        re.IGNORECASE,
    ),
    "external_purchase": re.compile(
        r"\b(external purchase|buy on web|license key|promo code|checkout\.stripe|paypal\.com|manage subscription|billing portal)\b",
        re.IGNORECASE,
    ),
    "ugc_or_social": re.compile(
        r"\b(user generated|UGC|comment|chat|message|post|feed|creator|follow|friend|report abuse|block user|moderation|flag content)\b",
        re.IGNORECASE,
    ),
    "report_block_moderate": re.compile(
        r"\b(report|block|moderation|moderate|flag|abuse|mute|hide user)\b",
        re.IGNORECASE,
    ),
    "tracking_or_ads": re.compile(
        r"\b(AppTrackingTransparency|NSUserTrackingUsageDescription|IDFA|advertisingIdentifier|AdMob|AppsFlyer|AdjustSDK|AdjustConfig|AdjustEvent|targeted ads|ad tracking|user tracking)\b",
        re.IGNORECASE,
    ),
    "third_party_sdk": re.compile(
        r"\b(Firebase|Crashlytics|Sentry|Amplitude|Segment|Mixpanel|RevenueCat|Supabase|Stripe|OneSignal|Intercom|OpenAI|GoogleService-Info)\b",
        re.IGNORECASE,
    ),
    "permissions_api": re.compile(
        r"\b(CLLocation|AVCapture|PHPhotoLibrary|PhotosPicker|CNContact|Contacts|HKHealthStore|HealthKit|CBPeripheral|Bluetooth|Microphone|Camera|UNUserNotificationCenter)\b",
        re.IGNORECASE,
    ),
    "private_or_risky_api": re.compile(
        r"\b(performSelector|NSClassFromString|dlopen|dlsym|private API|UIApplication\.shared|openURL|LSApplicationQueriesSchemes)\b",
        re.IGNORECASE,
    ),
    "background_modes": re.compile(
        r"\b(UIBackgroundModes|remote-notification|voip|location|audio|bluetooth-central|background fetch|BGTaskScheduler)\b",
        re.IGNORECASE,
    ),
    "apple_services": re.compile(
        r"\b(MusicKit|Apple Music|Apple Pay|Wallet|PassKit|GameKit|Game Center|Push Notifications|CloudKit|Sign in with Apple|AuthenticationServices)\b",
        re.IGNORECASE,
    ),
    "third_party_brands": re.compile(
        r"\b(Spotify|YouTube|Google|Facebook|Instagram|TikTok|Twitter|X\.com|Amazon|Netflix|Disney)\b",
        re.IGNORECASE,
    ),
    "regulated": re.compile(
        r"\b(medical|diagnos|treatment|therapy|health|fitness|gambling|crypto|bank|finance|loan|cannabis|legal advice|emergency)\b",
        re.IGNORECASE,
    ),
}

USAGE_DESCRIPTION_KEYS = re.compile(r"^NS[A-Za-z]+UsageDescription$")


@dataclass
class Match:
    path: Path
    line: int
    text: str


@dataclass
class Finding:
    status: str
    title: str
    detail: str
    evidence: list[str] = field(default_factory=list)


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d.lower() not in SKIP_DIRS_LOWER]
        current = Path(dirpath)
        for filename in filenames:
            yield current / filename


def iter_dirs(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, _filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d.lower() not in SKIP_DIRS_LOWER]
        current = Path(dirpath)
        for dirname in dirnames:
            yield current / dirname


def is_text_candidate(path: Path) -> bool:
    if path.suffix in TEXT_EXTS:
        return True
    return path.name in {
        "Podfile",
        "Cartfile",
        "Gemfile",
        "Package.swift",
        "project.pbxproj",
        "firebase.json",
        "app.json",
        "app.config.js",
    }


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def collect_matches(root: Path) -> tuple[dict[str, list[Match]], list[Path]]:
    matches: dict[str, list[Match]] = {key: [] for key in PATTERNS}
    text_files: list[Path] = []
    for path in iter_files(root):
        if not is_text_candidate(path):
            continue
        text = read_text(path)
        if text is None:
            continue
        text_files.append(path)
        for idx, line in enumerate(text.splitlines(), 1):
            clean = line.strip()
            if not clean:
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(clean):
                    bucket = matches[name]
                    if len(bucket) < 40:
                        bucket.append(Match(path=path, line=idx, text=clean[:180]))
    return matches, text_files


def find_by_suffix(root: Path, suffix: str) -> list[Path]:
    return sorted(p for p in iter_files(root) if p.name.endswith(suffix))


def find_dirs_by_suffix(root: Path, suffix: str) -> list[Path]:
    return sorted(p for p in iter_dirs(root) if p.name.endswith(suffix))


def find_named(root: Path, names: set[str]) -> list[Path]:
    lowered = {name.lower() for name in names}
    return sorted(p for p in iter_files(root) if p.name.lower() in lowered)


def parse_plists(paths: list[Path]) -> list[tuple[Path, dict]]:
    parsed: list[tuple[Path, dict]] = []
    for path in paths:
        try:
            with path.open("rb") as handle:
                data = plistlib.load(handle)
            if isinstance(data, dict):
                parsed.append((path, data))
        except Exception:
            continue
    return parsed


def format_matches(matches: list[Match], root: Path, limit: int = 8) -> list[str]:
    return [f"{rel(m.path, root)}:{m.line}: {m.text}" for m in matches[:limit]]


def is_doc_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root) if path.is_relative_to(root) else path
    if path.name in DOC_FILE_NAMES or path.suffix.lower() in {".md", ".txt"}:
        return True
    return any(part.lower() in DOC_DIR_NAMES for part in relative.parts)


def has_non_doc_match(matches: list[Match], root: Path) -> bool:
    return any(not is_doc_path(match.path, root) for match in matches)


def split_match_evidence(matches: list[Match], root: Path, limit: int = 8) -> list[str]:
    non_doc = [m for m in matches if not is_doc_path(m.path, root)]
    doc = [m for m in matches if is_doc_path(m.path, root)]
    return format_matches([*non_doc, *doc], root, limit)


def usage_description_summary(plists: list[tuple[Path, dict]], root: Path) -> list[str]:
    lines: list[str] = []
    for path, data in plists:
        keys = sorted(k for k in data if USAGE_DESCRIPTION_KEYS.match(str(k)))
        if keys:
            lines.append(f"{rel(path, root)}: {', '.join(keys)}")
    return lines


def summarize_bundle_ids(plists: list[tuple[Path, dict]], root: Path) -> list[str]:
    lines: list[str] = []
    for path, data in plists:
        bundle_id = data.get("CFBundleIdentifier")
        display_name = data.get("CFBundleDisplayName") or data.get("CFBundleName")
        version = data.get("CFBundleShortVersionString")
        build = data.get("CFBundleVersion")
        pieces = []
        if display_name:
            pieces.append(f"name={display_name}")
        if bundle_id:
            pieces.append(f"bundle={bundle_id}")
        if version:
            pieces.append(f"version={version}")
        if build:
            pieces.append(f"build={build}")
        if pieces:
            lines.append(f"{rel(path, root)}: {', '.join(pieces)}")
    return lines


def add_presence_finding(
    findings: list[Finding],
    title: str,
    present: bool,
    present_detail: str,
    absent_detail: str,
    evidence: list[str],
    absent_status: str = "UNKNOWN",
) -> None:
    findings.append(
        Finding(
            status="INFO" if present else absent_status,
            title=title,
            detail=present_detail if present else absent_detail,
            evidence=evidence,
        )
    )


def build_findings(root: Path, matches: dict[str, list[Match]], text_files: list[Path]) -> tuple[list[Finding], dict[str, list[Path]], list[tuple[Path, dict]]]:
    found = {
        "xcode_projects": find_dirs_by_suffix(root, ".xcodeproj"),
        "xcworkspaces": find_dirs_by_suffix(root, ".xcworkspace"),
        "plist": find_by_suffix(root, "Info.plist"),
        "entitlements": find_by_suffix(root, ".entitlements"),
        "privacy_manifest": find_by_suffix(root, "PrivacyInfo.xcprivacy"),
        "project_yml": find_named(root, {"project.yml", "xcodegen.yml"}),
        "package_swift": find_named(root, {"Package.swift"}),
        "podfile": find_named(root, {"Podfile"}),
        "capacitor": find_named(root, {"capacitor.config.ts", "capacitor.config.json"}),
        "expo": find_named(root, {"app.json", "app.config.js", "app.config.ts"}),
    }
    plists = parse_plists(found["plist"])

    findings: list[Finding] = []

    app_evidence = [
        *(rel(p, root) for p in found["xcode_projects"][:5]),
        *(rel(p, root) for p in found["xcworkspaces"][:5]),
        *(rel(p, root) for p in found["project_yml"][:5]),
        *(rel(p, root) for p in found["package_swift"][:5]),
        *(rel(p, root) for p in found["capacitor"][:5]),
        *(rel(p, root) for p in found["expo"][:5]),
    ]
    add_presence_finding(
        findings,
        "Apple app project signals",
        bool(app_evidence),
        "Found local project/config files that can anchor the audit.",
        "No Xcode or Apple app config files were detected. Confirm the path points at the app root.",
        app_evidence,
        absent_status="BLOCKER",
    )

    bundle_evidence = summarize_bundle_ids(plists, root)
    add_presence_finding(
        findings,
        "Bundle metadata",
        bool(bundle_evidence),
        "Found bundle identifiers/version metadata in Info.plist files.",
        "No readable bundle identifier/version metadata found. Verify generated plists or build settings manually.",
        bundle_evidence[:10],
    )

    usage_evidence = usage_description_summary(plists, root)
    permission_hits = format_matches(matches["permissions_api"], root)
    if permission_hits and not usage_evidence:
        findings.append(
            Finding(
                status="HIGH",
                title="Permission APIs found without readable purpose-string evidence",
                detail="Code references protected resources or notifications, but the scan did not find NS*UsageDescription keys. Verify generated plists and purpose strings.",
                evidence=permission_hits,
            )
        )
    else:
        findings.append(
            Finding(
                status="INFO",
                title="Permission and purpose-string review",
                detail="Review purpose strings against actual permission use and data minimization.",
                evidence=[*usage_evidence[:10], *permission_hits[:5]],
            )
        )

    add_presence_finding(
        findings,
        "Privacy manifest",
        bool(found["privacy_manifest"]),
        "Found PrivacyInfo.xcprivacy files. Verify SDK/data declarations match actual collection and App Store privacy labels.",
        "No PrivacyInfo.xcprivacy file found. This may be acceptable for some apps, but verify current Apple privacy manifest requirements and third-party SDK usage.",
        [rel(p, root) for p in found["privacy_manifest"][:10]],
    )

    if matches["placeholder_release_content"]:
        status = "HIGH" if has_non_doc_match(matches["placeholder_release_content"], root) else "INFO"
        findings.append(
            Finding(
                status=status,
                title="Placeholder/debug/staging strings",
                detail="Release builds should not expose placeholder text, debug affordances, staging endpoints, or temporary content. Documentation-only matches are lower signal but should still be checked against release assets.",
                evidence=split_match_evidence(matches["placeholder_release_content"], root),
            )
        )

    if matches["login_or_auth"] and not matches["account_deletion"]:
        findings.append(
            Finding(
                status="HIGH",
                title="Account/auth signals without account-deletion evidence",
                detail="If the app supports account creation, verify in-app account deletion and reviewer access/demo instructions.",
                evidence=format_matches(matches["login_or_auth"], root),
            )
        )
    elif matches["login_or_auth"]:
        findings.append(
            Finding(
                status="INFO",
                title="Account/auth review needed",
                detail="Verify reviewer access, demo mode or demo account, account deletion, and login requirement justification.",
                evidence=[*format_matches(matches["login_or_auth"], root, 5), *format_matches(matches["account_deletion"], root, 5)],
            )
        )

    if matches["payments"] or matches["external_purchase"]:
        status = "HIGH" if has_non_doc_match(matches["external_purchase"], root) else "INFO"
        findings.append(
            Finding(
                status=status,
                title="Payments or purchase flows",
                detail="Map the business model to Apple's in-app purchase, subscription, and external purchase link rules before submission.",
                evidence=[*split_match_evidence(matches["payments"], root, 6), *split_match_evidence(matches["external_purchase"], root, 6)],
            )
        )

    if matches["ugc_or_social"]:
        moderation_evidence = format_matches(matches["report_block_moderate"], root, 8)
        status = "INFO" if moderation_evidence else "HIGH"
        findings.append(
            Finding(
                status=status,
                title="User-generated or social content signals",
                detail="Verify filtering, report abuse, blocking, support contact, moderation response path, and age-rating alignment.",
                evidence=[*format_matches(matches["ugc_or_social"], root, 8), *moderation_evidence],
            )
        )

    if matches["tracking_or_ads"]:
        status = "HIGH" if has_non_doc_match(matches["tracking_or_ads"], root) else "INFO"
        findings.append(
            Finding(
                status=status,
                title="Tracking or ads signals",
                detail="Verify ATT, consent, privacy labels, ad appropriateness, and opt-out behavior. Ignore typography-only uses of the word tracking after manual inspection.",
                evidence=split_match_evidence(matches["tracking_or_ads"], root),
            )
        )

    if matches["third_party_sdk"]:
        findings.append(
            Finding(
                status="INFO",
                title="Third-party SDK/data processors",
                detail="Compare SDK data collection against PrivacyInfo.xcprivacy, App Store privacy labels, and the privacy policy.",
                evidence=format_matches(matches["third_party_sdk"], root),
            )
        )

    if matches["private_or_risky_api"]:
        status = "HIGH" if has_non_doc_match(matches["private_or_risky_api"], root) else "INFO"
        findings.append(
            Finding(
                status=status,
                title="Risky API or extension-safety patterns",
                detail="Verify all APIs are public, app-extension safe where required, and not used to bypass system behavior. Documentation-only warnings are lower signal.",
                evidence=split_match_evidence(matches["private_or_risky_api"], root),
            )
        )

    if matches["background_modes"]:
        findings.append(
            Finding(
                status="INFO",
                title="Background modes or notification paths",
                detail="Verify background modes and notifications are directly related to app functionality and not required for core access.",
                evidence=format_matches(matches["background_modes"], root),
            )
        )

    if matches["apple_services"]:
        findings.append(
            Finding(
                status="INFO",
                title="Apple services",
                detail="Verify service-specific rules, disclosure, entitlement usage, branding, and monetization restrictions.",
                evidence=format_matches(matches["apple_services"], root),
            )
        )

    if matches["third_party_brands"]:
        findings.append(
            Finding(
                status="INFO",
                title="Third-party brand references",
                detail="Verify app name, icon, screenshots, keywords, metadata, and UI do not misuse another developer's brand.",
                evidence=format_matches(matches["third_party_brands"], root),
            )
        )

    if matches["regulated"]:
        findings.append(
            Finding(
                status="HIGH",
                title="Regulated or sensitive domain signals",
                detail="Verify legal entity requirements, licenses, disclaimers, geofencing, and legal/privacy review.",
                evidence=format_matches(matches["regulated"], root),
            )
        )

    if not matches["privacy_support_terms"]:
        findings.append(
            Finding(
                status="HIGH",
                title="No privacy/support/terms text found",
                detail="Verify the app and App Store Connect metadata include accessible privacy policy and support contact links.",
                evidence=[],
            )
        )
    else:
        findings.append(
            Finding(
                status="INFO",
                title="Privacy/support/terms surfaces",
                detail="Verify these surfaces are live, accurate, and reachable from both App Store metadata and the app UI.",
                evidence=format_matches(matches["privacy_support_terms"], root),
            )
        )

    findings.append(
        Finding(
            status="MANUAL",
            title="App Store Connect-only gates",
            detail="Verify screenshots, preview videos, app description, keywords, category, age rating, privacy nutrition labels, review notes, demo credentials, IAP configuration, export compliance, and release settings in App Store Connect.",
            evidence=[],
        )
    )

    findings.append(
        Finding(
            status="MANUAL",
            title="Runtime verification",
            detail="Run the documented build/test/archive path and smoke-test first launch, core flows, reviewer access, account deletion, purchases, permissions, links, and extensions on simulator or device.",
            evidence=[],
        )
    )

    return findings, found, plists


def status_counts(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.status] = counts.get(finding.status, 0) + 1
    return counts


def suggested_verdict(findings: list[Finding]) -> str:
    if any(f.status == "BLOCKER" for f in findings):
        return "Not ready"
    if any(f.status == "HIGH" for f in findings):
        return "Conditionally ready"
    return "Conditionally ready"


def markdown_report(root: Path, findings: list[Finding], found: dict[str, list[Path]], plists: list[tuple[Path, dict]]) -> str:
    today = dt.date.today().isoformat()
    counts = status_counts(findings)
    verdict = suggested_verdict(findings)
    lines: list[str] = []
    lines.append("# App Store Review Audit")
    lines.append("")
    lines.append(f"Verdict: {verdict}")
    lines.append(f"Audit date: {today}")
    lines.append(f"Project path: `{root}`")
    lines.append("Policy source to refresh: https://developer.apple.com/app-store/review/guidelines/")
    lines.append("")
    lines.append("## Scanner Summary")
    lines.append("")
    lines.append("This report is a heuristic first pass. Verify every item manually against current Apple policy and the running app.")
    lines.append("")
    for status in ["BLOCKER", "HIGH", "UNKNOWN", "MANUAL", "INFO"]:
        if counts.get(status):
            lines.append(f"- {status}: {counts[status]}")
    lines.append("")
    lines.append("## Candidate Signals")
    lines.append("")
    signal_rows = [
        ("Xcode projects", found["xcode_projects"]),
        ("Workspaces", found["xcworkspaces"]),
        ("Info.plist files", found["plist"]),
        ("Entitlements", found["entitlements"]),
        ("Privacy manifests", found["privacy_manifest"]),
        ("XcodeGen/project YAML", found["project_yml"]),
        ("Swift packages", found["package_swift"]),
        ("Podfiles", found["podfile"]),
        ("Capacitor config", found["capacitor"]),
        ("Expo config", found["expo"]),
    ]
    for label, paths in signal_rows:
        if paths:
            joined = ", ".join(f"`{rel(p, root)}`" for p in paths[:8])
            extra = "" if len(paths) <= 8 else f" (+{len(paths) - 8} more)"
            lines.append(f"- {label}: {joined}{extra}")
    if not any(paths for _, paths in signal_rows):
        lines.append("- No Apple project signals detected.")
    lines.append("")
    bundle_lines = summarize_bundle_ids(plists, root)
    if bundle_lines:
        lines.append("## Bundle Metadata")
        lines.append("")
        for item in bundle_lines[:12]:
            lines.append(f"- `{item}`")
        lines.append("")
    lines.append("## Findings")
    lines.append("")
    for finding in findings:
        lines.append(f"### [{finding.status}] {finding.title}")
        lines.append("")
        lines.append(finding.detail)
        if finding.evidence:
            lines.append("")
            lines.append("Evidence:")
            for item in finding.evidence:
                lines.append(f"- `{item}`")
        lines.append("")
    lines.append("## Manual Review Checklist")
    lines.append("")
    checklist = [
        "Build/archive succeeds for the exact candidate version and build.",
        "First launch and core flows are tested on device or simulator.",
        "Reviewer has demo account, demo mode, seed data, invite codes, hardware, and notes needed for full access.",
        "Backend services and URLs are live during review.",
        "App Store metadata, screenshots, previews, privacy labels, age rating, and What's New text match the app.",
        "Privacy policy and support URL are live and reachable from App Store Connect and in app.",
        "Account creation, deletion, consent withdrawal, notification opt-out, and data retention behavior are verified.",
        "IAP/subscriptions/external purchase links are configured and compliant.",
        "Extensions, widgets, App Clips, notifications, background modes, and entitlements are disclosed and justified.",
        "No placeholders, debug UI, hidden features, or staging endpoints remain in release builds.",
    ]
    for item in checklist:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append("## App Review Notes Draft")
    lines.append("")
    lines.append("TODO: Explain reviewer access, non-obvious flows, purchases/subscriptions, entitlements, backend dependencies, demo data, and any required test setup.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a heuristic App Store review audit scaffold.")
    parser.add_argument("project", nargs="?", default=".", help="Path to the app project root.")
    parser.add_argument("--output", "-o", help="Write Markdown report to this path. Defaults to stdout.")
    args = parser.parse_args()

    root = Path(args.project).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        parser.error(f"Project path is not a directory: {root}")

    matches, text_files = collect_matches(root)
    findings, found, plists = build_findings(root, matches, text_files)
    report = markdown_report(root, findings, found, plists)

    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report + "\n", encoding="utf-8")
        print(f"Wrote {output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
