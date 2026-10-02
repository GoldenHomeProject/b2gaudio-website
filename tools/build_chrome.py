#!/usr/bin/env python3
"""Write the shared site chrome into every page, from one data file.

    python3 tools/build_chrome.py

Reads tools/apps.json and, for every *.html page at the site root:
  * the <head> block   (<!-- site-head:start/end -->)   site-chrome.css + .js, and a favicon if the page has none
  * the header         (<!-- site-header:start/end -->) studio mark -> apps hub, Apps menu, the page's app
                                                         (icon + name, Home/Guides/Support/Privacy, Get the app)
  * the footer         (<!-- site-footer:start/end -->) every app's links, the hub, contact, copyright
  * on each app's home page, a "More apps" strip (<!-- more-apps:start/end -->)
It also regenerates apps.html (the hub) and sitemap.xml, and tags every App Store link it writes with
its campaign (same rule as tools/tag_store_links.py, which is still worth running after hand edits).

Idempotent: blocks are rewritten in place, so running it twice changes nothing. A page that has no
markers yet is migrated once: its old <nav>...</nav> becomes the header block and its old
<footer>...</footer> becomes the footer block. Everything else on the page is left byte-for-byte alone.

Which app a page belongs to comes from each app's "pages" globs in apps.json. A page that matches
no app gets the studio header (hub pages); the script refuses to guess for anything else.
"""
from __future__ import annotations

import datetime
import fnmatch
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tag_store_links import campaign_for, tag  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((Path(__file__).with_name("apps.json")).read_text())
SITE, APPS = DATA["site"], DATA["apps"]
HUB = SITE["hub"]

MARK = "studio-mark.svg"
STORE = "https://apps.apple.com/app/apple-store/id{}"   # tag_store_links.py adds pt/ct/mt
SKIP = ("google*.html", "_*.html")                       # verification file, fragments
NOT_APP_PAGES = {HUB}                                    # pages that belong to the studio, not an app

APPLE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79'
         '-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 '
         '3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 '
         '1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 '
         '1.05-3.11z"/></svg>')
CARET = ('<svg class="sh-caret" viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" '
         'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')

esc = lambda s: html.escape(s, quote=True)


def start(name): return f"<!-- {name}:start -->"
def end(name): return f"<!-- {name}:end -->"


# ---------------------------------------------------------------- data helpers

def live(app): return app["status"] == "live"
def store(app): return STORE.format(app["app_store_id"]) if live(app) else None


def file_of(href: str | None) -> str | None:
    """The page file an internal href points at ('/' is index.html); None for in-page anchors."""
    if not href or "#" in href:
        return None
    return "index.html" if href in ("/", "/index.html") else href.lstrip("/")


def home_file(app): return file_of(app["home"])


def app_for(page: str):
    if page in NOT_APP_PAGES:
        return None
    hits = [a for a in APPS if any(fnmatch.fnmatch(page, g) for g in a["pages"])]
    if len(hits) != 1:
        sys.exit(f"build_chrome: {page} matches {len(hits)} apps in apps.json — add it to exactly one app's \"pages\"")
    return hits[0]


def current(href, page):
    return ' aria-current="page"' if file_of(href) == page else ""


def badge(app):
    return '<span class="sh-badge">Coming soon</span>' if not live(app) else ""


def app_links(app):
    """The per-app links, in header order. Guides only when the app has some."""
    out = [("Home", app["home"])]
    if app.get("guides"):
        out.append(("Guides", app["guides"]))
    out += [("Support", app["support"]), ("Privacy", app["privacy"])]
    return out


# ---------------------------------------------------------------- renderers

def applinks(cur_app):
    rows = []
    for a in APPS:
        cur = ' aria-current="true"' if cur_app is a else ""
        rows.append(
            f'<a class="sh-applink" href="{a["home"]}" style="--a:{a["accent"]}"{cur}>'
            f'<img src="{a["icon"]}" alt="" width="40" height="40">'
            f'<span><b>{esc(a["name"])}{badge(a)}</b><small>{esc(a["tagline"])}</small></span></a>')
    rows.append(f'<a class="sh-all" href="{HUB}">See all apps <span aria-hidden="true">&rarr;</span></a>')
    return "\n".join(rows)


def cta(app):
    if live(app):
        return (f'<a class="sh-cta" href="{store(app)}" aria-label="Get {esc(app["name"])} on the App Store">{APPLE}'
                f'<span class="sh-cta-long">Get the app</span><span class="sh-cta-short">Get</span></a>')
    return '<span class="sh-soon">Coming soon</span>'


def render_header(page, app):
    studio = (f'<a class="sh-studio" href="{HUB}" aria-label="{esc(SITE["studio"])}: all apps"{current(HUB, page)}>'
              f'<img class="sh-mark" src="{MARK}" alt="" width="30" height="30">'
              f'<span class="sh-studio-name">{esc(SITE["studio"])}</span></a>')
    apps_menu = (f'<details class="sh-apps"><summary>Apps {CARET}</summary>\n'
                 f'<div class="sh-apps-panel">\n{applinks(app)}\n</div></details>')
    if app is None:
        style, cls = "", "sh sh-hub"
        middle = '<span class="sh-spacer"></span>'
        menu_app = ""
    else:
        style = f' style="--sh-accent:{app["accent"]};--sh-accent-text:{app["accent_text"]}"'
        cls = "sh sh-app-page"
        links = "".join(f'<a href="{h}"{current(h, page)}>{t}</a>' for t, h in app_links(app))
        middle = (f'<span class="sh-div" aria-hidden="true"></span>\n'
                  f'<a class="sh-app" href="{app["home"]}"{current(app["home"], page)}>'
                  f'<img src="{app["icon"]}" alt="" width="30" height="30"><span>{esc(app["name"])}</span></a>\n'
                  f'<nav class="sh-links" aria-label="{esc(app["name"])}">{links}</nav>\n'
                  f'<span class="sh-spacer"></span>\n{cta(app)}')
        mlinks = "".join(f'<a href="{h}"{current(h, page)}>{t}</a>'
                         for t, h in app_links(app) + [("Terms", app["terms"])])
        if live(app):
            mlinks += (f'<a class="sh-cta" href="{store(app)}">{APPLE}Get {esc(app["name"])} on the App Store</a>')
        menu_app = (f'<div class="sh-menu-h"><img src="{app["icon"]}" alt="" width="18" height="18">'
                    f'{esc(app["name"])}{badge(app)}</div>\n'
                    f'<nav class="sh-menu-links" aria-label="{esc(app["name"])}">{mlinks}</nav>\n')
    menu = (f'<details class="sh-menu"><summary><span class="sh-vh">Menu</span><i></i><i></i><i></i></summary>\n'
            f'<div class="sh-menu-panel">\n{menu_app}'
            f'<div class="sh-menu-h">All apps</div>\n<nav aria-label="All apps">\n{applinks(app)}\n</nav>\n'
            f'</div></details>')
    return (f'<header class="{cls}"{style}>\n<div class="sh-bar">\n{studio}\n{apps_menu}\n{middle}\n{menu}\n'
            f'</div>\n</header>')


def render_footer(page, app):
    cols = []
    for a in APPS:
        items = []
        if a.get("guides"):
            items.append(("Guides", a["guides"]))
        items += [("Support", a["support"]), ("Privacy Policy", a["privacy"]), ("Terms of Service", a["terms"])]
        if live(a):
            items.append(("App Store", store(a)))
        lis = "".join(f'<li><a href="{h}"{current(h, page)}>{t}</a></li>' for t, h in items)
        cols.append(
            f'<div class="sf-app" style="--a:{a["accent"]}"><p class="sf-app-h">'
            f'<a href="{a["home"]}"{current(a["home"], page)}><img src="{a["icon"]}" alt="" width="22" height="22">'
            f'{esc(a["name"])}</a>{badge(a)}</p><ul>{lis}</ul></div>')
    mail = SITE["contact_email"]
    return (f'<footer class="sf">\n<div class="sf-inner">\n<div class="sf-top">\n'
            f'<div class="sf-brand"><a class="sf-brand-link" href="{HUB}"><img class="sh-mark" src="{MARK}" alt="" '
            f'width="30" height="30">{esc(SITE["studio"])}</a>\n'
            f'<p>Every app we make, what it does, and where to get it.</p>\n'
            f'<div class="sf-brand-links"><a href="{HUB}">All apps</a><a href="mailto:{mail}">Contact</a></div></div>\n'
            f'<nav class="sf-apps" aria-label="Apps">\n' + "\n".join(cols) + '\n</nav>\n</div>\n'
            f'<div class="sf-bottom"><p class="copyright">{SITE["copyright"]}</p>'
            f'<div><a href="{HUB}">All apps</a><a href="mailto:{mail}">{mail}</a></div></div>\n'
            f'</div>\n</footer>')


def render_more(page, app):
    others = [a for a in APPS if a is not app]
    cards = "\n".join(
        f'<a class="sm-card" href="{a["home"]}" style="--a:{a["accent"]}">'
        f'<img src="{a["icon"]}" alt="" width="52" height="52">'
        f'<span><b>{esc(a["name"])}{badge(a)}</b><small>{esc(a["tagline"])}</small>'
        f'<span class="sm-more">Learn more &rarr;</span></span></a>' for a in others)
    return (f'<section class="sm" aria-labelledby="sm-h">\n<div class="sm-inner">\n'
            f'<h2 class="sm-h" id="sm-h">More apps from {esc(SITE["studio"])}</h2>\n'
            f'<p class="sm-sub">From the people who make {esc(app["name"])}.</p>\n'
            f'<div class="sm-grid">\n{cards}\n</div>\n'
            f'<a class="sm-all" href="{HUB}">See all apps &rarr;</a>\n</div>\n</section>')


def render_head(page, app, page_html):
    out = ['<link rel="stylesheet" href="site-chrome.css">', '<script src="site-chrome.js" defer></script>']
    if 'rel="icon"' not in page_html:             # several legal pages never had one
        if app is None:
            out.append(f'<link rel="icon" type="image/svg+xml" href="{MARK}">')
        else:
            out.append(f'<link rel="icon" type="image/png" href="{app["icon"]}">')
    return "\n".join(out)


def render_hub():
    base = SITE["base_url"]
    cards = []
    for a in APPS:
        s = store(a)
        status = ('<span class="hub-status">Live on the App Store</span>' if s
                  else '<span class="hub-status soon">Coming soon</span>')
        actions = []
        if s:
            actions.append(f'<a class="hub-btn primary" href="{s}" aria-label="Download {esc(a["name"])} on the App Store">'
                           f'{APPLE}App Store</a>')
            actions.append(f'<a class="hub-btn ghost" href="{a["home"]}">Learn more</a>')
        else:
            actions.append(f'<a class="hub-btn primary" href="{a["home"]}">Learn more</a>')
            actions.append('<span class="hub-btn disabled">Not on the App Store yet</span>')
        links = [("Guides", a.get("guides")), ("Support", a["support"]), ("Privacy", a["privacy"]), ("Terms", a["terms"])]
        links = "".join(f'<a href="{h}">{t}</a>' for t, h in links if h)
        cards.append(f"""<article class="hub-card" id="{a['id']}" style="--a:{a['accent']};--at:{a['accent_text']}">
  <div class="hub-card-top"><img src="{a['icon']}" alt="{esc(a['name'])} app icon" width="68" height="68">
    <div><h2><a href="{a['home']}" style="color:inherit">{esc(a['name'])}</a></h2>{status}</div></div>
  <p class="hub-tagline">{esc(a['tagline'])}</p>
  <p class="hub-summary">{esc(a['summary'])}</p>
  <p class="hub-platform">{esc(a['platform'])}</p>
  <div class="hub-actions">{''.join(actions)}</div>
  <div class="hub-links">{links}</div>
</article>""")
    ld = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": SITE["hub_title"], "url": base + HUB, "description": SITE["hub_description"],
        "publisher": {"@type": "Organization", "name": SITE["studio"]},
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": a["name"],
             "url": base + (a["home"].lstrip("/"))} for i, a in enumerate(APPS, 1)]},
    }
    title, desc = SITE["hub_title"], SITE["hub_description"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<!-- Generated by tools/build_chrome.py from tools/apps.json. Do not edit by hand. -->
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{base}{HUB}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE['studio'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{base}{HUB}">
<meta property="og:image" content="{base}studio-mark.png">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{base}studio-mark.png">
<link rel="apple-touch-icon" href="studio-mark.png">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0A0A0F;color:#F5F5F7;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}}
</style>
<script type="application/ld+json">
{json.dumps(ld, ensure_ascii=False, indent=1)}
</script>
{start('site-head')}
{end('site-head')}
</head>
<body>
{start('site-header')}
{end('site-header')}
<main class="hub">
  <div class="hub-hero">
    <img src="{MARK}" alt="" width="64" height="64">
    <h1>{esc(title)}</h1>
    <p>Every app we make, in one place: what each one does, and where to get it.</p>
  </div>
  <div class="hub-grid">
{chr(10).join(cards)}
  </div>
  <p class="hub-note">Questions about any of them? Email <a href="mailto:{SITE['contact_email']}">{SITE['contact_email']}</a>.</p>
</main>
{start('site-footer')}
{end('site-footer')}
</body>
</html>
"""


# ---------------------------------------------------------------- page surgery

APP_MENU = re.compile(r"\n?<!-- app-menu:start -->.*?<!-- app-menu:end -->\n?", re.S)
OLD_NAV = re.compile(r'<nav>\s*<div class="nav-inner">.*?</nav>', re.S)
OLD_FOOTER = re.compile(r"<footer>.*?</footer>", re.S)


def block_re(name):
    return re.compile(re.escape(start(name)) + r".*?" + re.escape(end(name)), re.S)


def migrate(page, src, app):
    """One-time: swap a page's old nav/footer for empty marker blocks."""
    if start("site-header") not in src:
        src = APP_MENU.sub("\n", src)
        if len(OLD_NAV.findall(src)) != 1:
            sys.exit(f"build_chrome: {page}: expected exactly one old <nav><div class=\"nav-inner\"> to replace")
        src = OLD_NAV.sub(lambda m: f"{start('site-header')}\n{end('site-header')}", src, count=1)
    if start("site-footer") not in src:
        if len(OLD_FOOTER.findall(src)) != 1:
            sys.exit(f"build_chrome: {page}: expected exactly one old <footer> to replace")
        src = OLD_FOOTER.sub(lambda m: f"{start('site-footer')}\n{end('site-footer')}", src, count=1)
    if start("site-head") not in src:
        src = src.replace("</head>", f"{start('site-head')}\n{end('site-head')}\n</head>", 1)
    if app and page == home_file(app) and start("more-apps") not in src:
        src = src.replace(start("site-footer"), f"{start('more-apps')}\n{end('more-apps')}\n\n{start('site-footer')}", 1)
    return src


def fill(src, name, body):
    pat = block_re(name)
    if len(pat.findall(src)) > 1:
        sys.exit(f"build_chrome: duplicate {name} blocks")
    return pat.sub(lambda m: f"{start(name)}\n{body}\n{end(name)}", src)


def build_page(path: Path, src: str | None = None):
    """Fill every block on one page; returns True if the file changed. `src` overrides the file (the hub)."""
    page = path.name
    app = app_for(page)
    before = path.read_text() if path.exists() else ""
    src = migrate(page, before if src is None else src, app)
    without_head_block = block_re("site-head").sub("", src)
    src = fill(src, "site-head", render_head(page, app, without_head_block))
    src = fill(src, "site-header", render_header(page, app))
    src = fill(src, "site-footer", render_footer(page, app))
    if start("more-apps") in src:
        src = fill(src, "more-apps", render_more(page, app))
    src = tag(src, campaign_for(path))
    if src != before:
        path.write_text(src)
        return True
    return False


# ---------------------------------------------------------------- sitemap

SM_ROW = re.compile(r"<url><loc>(.*?)</loc><lastmod>(.*?)</lastmod><priority>(.*?)</priority></url>")


def build_sitemap(pages):
    sm = ROOT / "sitemap.xml"
    old = {loc: (mod, pri) for loc, mod, pri in SM_ROW.findall(sm.read_text())}
    today = datetime.date.today().isoformat()
    rows = []
    for page in pages:
        loc = SITE["base_url"] + ("" if page == "index.html" else page)
        mod, pri = old.get(loc, (today, "0.7"))
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{mod}</lastmod><priority>{pri}</priority></url>")
    out = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n")
    if out != sm.read_text():
        sm.write_text(out)
        return True
    return False


def main():
    hub_changed = build_page(ROOT / HUB, render_hub())   # the hub is regenerated whole, every run

    pages = sorted(p for p in ROOT.glob("*.html") if not any(fnmatch.fnmatch(p.name, g) for g in SKIP))
    changed = [p.name for p in pages if p.name != HUB and build_page(p)] + ([HUB] if hub_changed else [])
    print(f"chrome written into {len(changed)} of {len(pages)} page(s)")
    for name in changed:
        print("  ", name)
    if build_sitemap([p.name for p in pages]):
        print("sitemap.xml updated")


if __name__ == "__main__":
    main()
