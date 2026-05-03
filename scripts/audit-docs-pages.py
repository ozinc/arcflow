#!/usr/bin/env python3
"""Probe every /docs/<slug> on a deployed website and surface broken pages
or broken external links.

Pass 1 — page load probe per slug:
  - GET https://<base>/docs/<slug>
  - Extract the first <h1> inside <article ... data-docs-content>
  - Compare against the expected title from docs/_config.json
    (HTML-entity-decoded, case-insensitive substring match)
  - Missing article-h1 means MDX compilation threw and the docs route
    silently fell through to notFound() — surface it.

Pass 2 — external link audit:
  - Collect every <a href="https://..."> from all probed bodies
  - Dedupe; HEAD each unique URL
  - Skip own-origin and a small allowlist of hosts that legitimately
    appear without a navigable path (R2 base, analytics, blob storage)

Usage:
    scripts/audit-docs-pages.py [--base https://staging.oz.com]

Exit codes: 0 = clean, 1 = real findings, 2 = harness error.

This script is the regression check for the page-by-page docs audit;
extend the host allowlist and redirect-slug list as the docs surface
grows. Wire it into CI alongside scripts/lint-mdx-urls.py.
"""
from __future__ import annotations

import argparse
import json
import html as html_lib
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ARTICLE_RE = re.compile(
    r'<article[^>]*data-docs-content[^>]*>(.*?)</article>', re.DOTALL
)
H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.DOTALL)
TAG_STRIP_RE = re.compile(r'<[^>]+>')
HREF_RE = re.compile(r'href="(https?://[^"]+)"')

# Slugs that legitimately redirect to a non-docs route on the website.
# Add to this list when the website's REDIRECTS map grows.
REDIRECT_SLUGS = {
    "pricing",  # /docs/pricing → /pricing (see docs/[...slug]/page.tsx REDIRECTS)
}

# External hosts that legitimately appear in page HTML without a navigable
# path (CSP / preconnect / analytics / blob storage bases). HEAD requests
# to these bare hosts are expected to 404 or be unreachable; that is not
# a broken link.
EXTERNAL_HOST_ALLOWLIST = {
    "https://pub-a0a196dbe10340f8af22524547fdd476.r2.dev",  # R2 bucket base
    "https://vercel-storage.com",
    "https://www.googletagmanager.com",
}
EXTERNAL_PREFIX_ALLOWLIST = (
    "https://waqjo0bjh1oeizso.public.blob.vercel-storage.com",
    "http://localhost:",  # any dev port
)


def load_slug_titles() -> dict[str, str]:
    config = json.loads((ROOT / "docs" / "_config.json").read_text())
    out: dict[str, str] = {}
    for section in config.get("sections", []):
        for item in section.get("items", []):
            out[item["slug"]] = item.get("title", item["slug"])
    return out


def fetch(url: str, timeout: int = 30) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "docs-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def head(url: str, timeout: int = 20) -> int:
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "docs-audit/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def extract_article_h1(body: str) -> str | None:
    art = ARTICLE_RE.search(body)
    if not art:
        return None
    h1 = H1_RE.search(art.group(1))
    if not h1:
        return None
    text = TAG_STRIP_RE.sub('', h1.group(1)).strip()
    return html_lib.unescape(text)


def probe_slug(base: str, slug: str, expected_title: str) -> dict:
    url = f"{base}/docs/{slug}"
    status, body = fetch(url)
    flags: list[str] = []

    if status != 200:
        flags.append(f"http_{status}")

    if slug in REDIRECT_SLUGS:
        # Don't expect an article on a redirect target.
        actual_h1 = None
    else:
        actual_h1 = extract_article_h1(body) if body else None
        if actual_h1 is None:
            flags.append("no_article_h1")
        else:
            a = actual_h1.lower()
            e = html_lib.unescape(expected_title).lower()
            if e not in a and a not in e:
                flags.append(f"h1_mismatch:{actual_h1!r}")

    links = HREF_RE.findall(body or "")
    return {
        "slug": slug,
        "url": url,
        "status": status,
        "h1": actual_h1,
        "expected": expected_title,
        "flags": flags,
        "links": links,
    }


def is_external_skipped(link: str, base: str) -> bool:
    if link.startswith(base):
        return True
    if link in EXTERNAL_HOST_ALLOWLIST:
        return True
    if link.startswith(EXTERNAL_PREFIX_ALLOWLIST):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit deployed /docs/* pages.")
    parser.add_argument(
        "--base",
        default="https://staging.oz.com",
        help="Base URL of the deployed site (default: staging.oz.com)",
    )
    parser.add_argument(
        "--workers", type=int, default=12, help="Concurrent fetches (default: 12)"
    )
    args = parser.parse_args()

    slug_titles = load_slug_titles()
    print(f"probing {len(slug_titles)} pages on {args.base}...", file=sys.stderr)

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(probe_slug, args.base, s, t): s for s, t in slug_titles.items()}
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r["slug"])
    page_failures = [r for r in results if r["flags"]]

    external_links: set[str] = set()
    for r in results:
        for link in r["links"]:
            if not is_external_skipped(link, args.base):
                external_links.add(link)

    print(f"  pages probed: {len(results)}", file=sys.stderr)
    print(f"  pages with load issues: {len(page_failures)}", file=sys.stderr)
    print(f"  unique external links to check: {len(external_links)}", file=sys.stderr)

    link_results: list[tuple[str, int]] = []
    with ThreadPoolExecutor(max_workers=args.workers * 2) as ex:
        futures = {ex.submit(head, link): link for link in external_links}
        for fut in as_completed(futures):
            link_results.append((futures[fut], fut.result()))

    link_results.sort()
    bad_links = [(l, s) for l, s in link_results if s == 0 or s >= 400]

    # Classify page issues into hard failures (page broken) vs soft
    # warnings (h1_mismatch — sidebar title vs MDX h1 prose drift).
    hard_failures = [
        r for r in page_failures
        if any(not f.startswith("h1_mismatch:") for f in r["flags"])
    ]
    soft_warnings = [
        r for r in page_failures
        if all(f.startswith("h1_mismatch:") for f in r["flags"])
    ]

    print("\n=== HARD PAGE FAILURES (block) ===")
    if not hard_failures:
        print("  (none)")
    else:
        for r in hard_failures:
            print(f"  {r['url']}  status={r['status']}  flags={r['flags']}")

    if soft_warnings:
        print(f"\n=== SOFT WARNINGS — sidebar/h1 prose drift ({len(soft_warnings)}) ===")
        for r in soft_warnings:
            print(f"  {r['slug']}: config={r['expected']!r}  h1={r['h1']!r}")

    print("\n=== BROKEN EXTERNAL LINKS ===")
    if not bad_links:
        print("  (none)")
    else:
        for link, status in bad_links:
            tag = "404" if status == 404 else f"http_{status}" if status else "unreachable"
            print(f"  {tag}  {link}")

    return 0 if (not hard_failures and not bad_links) else 1


if __name__ == "__main__":
    sys.exit(main())
