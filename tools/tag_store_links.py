#!/usr/bin/env python3
"""Tag every App Store link on the site with an App Store Connect campaign.

Without a campaign token, App Store Connect lumps a download that came from
this site in with everything else, so there is no way to tell whether a page
is earning its keep. With `pt` (provider token) and `ct` (campaign), downloads
show up per page under Analytics → Acquisition → Campaigns.

Idempotent: links that already carry a campaign are rewritten to the same
canonical form, so re-running after gen_guides.py is safe.

    python3 tools/tag_store_links.py
"""
from __future__ import annotations

import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
PROVIDER_TOKEN = "128605371"  # Golden Home Project LLC, from ASC's campaign link generator
LINK = re.compile(r'href="https://apps\.apple\.com/[^"]*?id(\d+)[^"]*"')


def campaign_for(page: Path) -> str:
    # ct is capped at 40 characters by App Store Connect.
    return ("web-" + page.stem)[:40]


def tag(html: str, campaign: str) -> str:
    return LINK.sub(
        lambda m: (f'href="https://apps.apple.com/app/apple-store/id{m.group(1)}'
                   f'?pt={PROVIDER_TOKEN}&amp;ct={campaign}&amp;mt=8"'),
        html,
    )


def main() -> None:
    changed = 0
    for page in sorted(SITE.glob("*.html")):
        before = page.read_text()
        after = tag(before, campaign_for(page))
        if after != before:
            page.write_text(after)
            changed += 1
    print(f"tagged App Store links in {changed} page(s)")


if __name__ == "__main__":
    main()
