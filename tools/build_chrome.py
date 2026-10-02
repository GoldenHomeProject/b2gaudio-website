#!/usr/bin/env python3
"""Write the shared site chrome into every page, from one data file.

    python3 tools/build_chrome.py

Reads tools/apps.json and, for every *.html page at the site root, fills these marker blocks:
  * site-head    (<!-- site-head:start/end -->)    site-chrome.css + .js, and a favicon if the page has none
  * site-header  (<!-- site-header:start/end -->)  one row of app tabs: "All apps" (-> hub), then every app
                                                    by icon + name (current app highlighted), then the current
                                                    app's "Get the app" button. More than MAX_TABS apps -> "More".
  * site-footer  (<!-- site-footer:start/end -->)  every app's guides/support/privacy/terms, contact, copyright
  * app-help     (<!-- app-help:start/end -->)     on each app's home page: "Guides & help" (every guide page of
                                                    that app, plus Support / Privacy Policy / Terms of Service)
  * breadcrumb   (<!-- breadcrumb:start/end -->)   on every other app page: "App › Guides › Page", with a
                                                    separate BreadcrumbList JSON-LD block
  * more-apps    (<!-- more-apps:start/end -->)    on each app's home page: the other apps
It also regenerates apps.html (the hub) and sitemap.xml, and tags every App Store link it writes with
its campaign (same rule as tools/tag_store_links.py, which is still worth running after hand edits).

Guides are found, not listed: every page that matches an app's "pages" globs and is not its home,
support, privacy or terms page is a guide. Title = the page's <h1>; one-liner = the first sentence of its
meta description; order and short labels (breadcrumbs) = the app's optional "guides" list in apps.json,
with unlisted guides last, labelled by their <h1>. Adding a guide page and re-running this script puts it
in the home page's "Guides & help" and gives it a breadcrumb.

Idempotent: blocks are rewritten in place, so running it twice changes nothing. A page without markers
is migrated once (old <nav>/<footer> become the header/footer blocks; the other blocks are inserted at
fixed points). Everything outside the markers is left byte-for-byte alone.
"""
from __future__ import annotations

import datetime
import fnmatch
import html
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tag_store_links import campaign_for, tag  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((Path(__file__).with_name("apps.json")).read_text())
SITE, APPS = DATA["site"], DATA["apps"]
HUB = SITE["hub"]
BASE = SITE["base_url"]

MAX_TABS = 6                                             # apps shown as header tabs; the rest go under "More"
HELP_ID = "guides-help"                                  # anchor of the "Guides & help" section on app homes
HUB_ICON = "apps-icon.svg"                               # neutral favicon for the hub
HUB_OG = "og-apps.png"                                   # 1200x630, rendered from og-builder/apps-og.html
STORE = "https://apps.apple.com/app/apple-store/id{}"   # tag_store_links.py adds pt/ct/mt
SKIP = ("google*.html", "_*.html")                       # verification file, fragments
NOT_APP_PAGES = {HUB}                                    # pages that belong to no single app

APPLE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79'
         '-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 '
         '3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 '
         '1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 '
         '1.05-3.11z"/></svg>')
CARET = ('<svg class="sh-caret" viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" '
         'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
GRID = ('<svg class="sh-grid" viewBox="0 0 20 20" aria-hidden="true"><rect x="2" y="2" width="6.5" height="6.5" rx="1.8"/>'
        '<rect x="11.5" y="2" width="6.5" height="6.5" rx="1.8"/><rect x="2" y="11.5" width="6.5" height="6.5" rx="1.8"/>'
        '<rect x="11.5" y="11.5" width="6.5" height="6.5" rx="1.8"/></svg>')
DOC = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 2.5h6.5L15 6v11.5H5z" fill="none" stroke="currentColor" '
       'stroke-width="1.5" stroke-linejoin="round"/><path d="M7.5 9.5h5M7.5 12.5h5" stroke="currentColor" stroke-width="1.5" '
       'stroke-linecap="round"/></svg>')

esc = lambda s: html.escape(s, quote=True)


def start(name): return f"<!-- {name}:start -->"
def end(name): return f"<!-- {name}:end -->"


def block_re(name):
    return re.compile(re.escape(start(name)) + r".*?" + re.escape(end(name)), re.S)


ALL_BLOCKS = re.compile(r"<!-- ([a-z-]+):start -->.*?<!-- \1:end -->", re.S)

# ---------------------------------------------------------------- data helpers

def live(app): return app["status"] == "live"
def store(app): return STORE.format(app["app_store_id"]) if live(app) else None


def file_of(href: str | None) -> str | None:
    """The page file an internal href points at ('/' is index.html); None for in-page anchors."""
    if not href or "#" in href:
        return None
    return "index.html" if href in ("/", "/index.html") else href.lstrip("/")


def home_file(app): return file_of(app["home"])
def help_href(app): return f'{app["home"]}#{HELP_ID}'
def url_of(href): return BASE + ("" if href in ("/", "/index.html") else href.lstrip("/"))


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


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


@lru_cache(maxsize=None)
def page_meta(page: str):
    """(h1 text, meta description) of a page, read from its own content (never from the chrome)."""
    src = ALL_BLOCKS.sub("", (ROOT / page).read_text())
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', src)
    return (text_of(h1.group(1)) if h1 else page, html.unescape(desc.group(1)) if desc else "")


def first_sentence(s: str) -> str:
    m = re.match(r"(.+?[.!?])(\s|$)", s)
    return m.group(1) if m else s


@lru_cache(maxsize=None)
def curated(app_id: str):
    """{guide file: short label} from the app's optional "guides" list in apps.json, in that order."""
    app = next(a for a in APPS if a["id"] == app_id)
    return {f: short for f, short in app.get("guides", [])}


def special_pages(app):
    return {home_file(app): "Home", file_of(app["support"]): "Support",
            file_of(app["privacy"]): "Privacy Policy", file_of(app["terms"]): "Terms of Service"}


@lru_cache(maxsize=None)
def guides_of(app_id: str):
    """[(file, title, one-liner, short title)] for every guide page of an app."""
    app = next(a for a in APPS if a["id"] == app_id)
    special = special_pages(app)
    files = sorted(p.name for p in ROOT.glob("*.html")
                   if p.name not in special and p.name not in NOT_APP_PAGES
                   and not any(fnmatch.fnmatch(p.name, g) for g in SKIP)
                   and any(fnmatch.fnmatch(p.name, g) for g in app["pages"]))
    order = list(curated(app_id))
    missing = [f for f in order if f not in files]
    if missing:
        sys.exit(f"build_chrome: apps.json lists guides that don't exist: {', '.join(missing)}")
    files.sort(key=lambda f: (order.index(f) if f in order else len(order), f))
    out = []
    for f in files:
        title, desc = page_meta(f)
        out.append((f, title, first_sentence(desc), curated(app_id).get(f) or title))
    return out


# ---------------------------------------------------------------- header

def tab(a, page, cur_app):
    is_cur = a is cur_app
    aria = ' aria-current="page"' if file_of(a["home"]) == page else (' aria-current="true"' if is_cur else "")
    short = a.get("short", a["name"])
    pill = '<span class="sh-pill">Soon</span>' if not live(a) else ""
    return (f'<a class="sh-tab{" is-current" if is_cur else ""}" href="{a["home"]}" style="--a:{a["accent"]}"{aria}>'
            f'<img src="{a["icon"]}" alt="" width="24" height="24">'
            f'<span class="sh-name"><span class="sh-full">{esc(a["name"])}</span>'
            f'<span class="sh-short" aria-hidden="true">{esc(short)}</span></span>{pill}</a>')


def cta(app):
    if app is None:
        return ""
    if live(app):
        return (f'<a class="sh-cta" href="{store(app)}" aria-label="Get {esc(app["name"])} on the App Store">{APPLE}'
                f'<span class="sh-cta-long">Get the app</span><span class="sh-cta-short">Get</span></a>')
    return '<span class="sh-soon">Coming soon</span>'


def render_header(page, app):
    visible = APPS[:MAX_TABS]
    if len(APPS) > MAX_TABS and app is not None and app not in visible:
        visible = APPS[:MAX_TABS - 1] + [app]           # the current app always gets a tab
    extra = [a for a in APPS if a not in visible]
    all_tab = (f'<a class="sh-tab sh-tab-all" href="{HUB}" aria-label="All apps"{current(HUB, page)}>{GRID}'
               f'<span class="sh-name">All apps</span></a>')
    tabs = "\n".join([all_tab] + [tab(a, page, app) for a in visible])
    more = ""
    if extra:
        rows = "\n".join(
            f'<a class="sh-applink" href="{a["home"]}" style="--a:{a["accent"]}">'
            f'<img src="{a["icon"]}" alt="" width="36" height="36">'
            f'<span><b>{esc(a["name"])}{badge(a)}</b><small>{esc(a["tagline"])}</small></span></a>' for a in extra)
        more = (f'\n<details class="sh-more"><summary>More {CARET}</summary>\n'
                f'<div class="sh-more-panel">\n{rows}\n</div></details>')
    style = (f' style="--sh-accent:{app["accent"]};--sh-accent-text:{app["accent_text"]}"' if app else "")
    return (f'<header class="sh"{style}>\n<div class="sh-bar">\n'
            f'<nav class="sh-nav" aria-label="Our apps">\n<div class="sh-strip">\n{tabs}\n</div>{more}\n</nav>\n'
            f'{cta(app)}\n</div>\n</header>')


# ---------------------------------------------------------------- footer, more apps, help, breadcrumb

def render_footer(page, app):
    cols = []
    for a in APPS:
        items = []
        if guides_of(a["id"]):
            items.append(("Guides", help_href(a)))
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
            f'<div class="sf-brand"><a class="sf-brand-link" href="{HUB}">{GRID}All apps</a>\n'
            f'<p>Every app we make, what it does, and where to get it.</p>\n'
            f'<div class="sf-brand-links"><a href="mailto:{mail}">Contact us</a></div></div>\n'
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
            f'<h2 class="sm-h" id="sm-h">More apps from us</h2>\n'
            f'<p class="sm-sub">From the people who make {esc(app["name"])}.</p>\n'
            f'<div class="sm-grid">\n{cards}\n</div>\n'
            f'<a class="sm-all" href="{HUB}">See all apps &rarr;</a>\n</div>\n</section>')


def render_help(page, app):
    guides = guides_of(app["id"])
    cards = "\n".join(
        f'<a class="sg-card" href="{f}"><b>{esc(title)}</b><small>{esc(line)}</small>'
        f'<span class="sg-go">Read the guide &rarr;</span></a>' for f, title, line, _ in guides)
    links = "".join(f'<a class="sg-link" href="{h}">{DOC}{t}</a>' for t, h in
                    [("Support", app["support"]), ("Privacy Policy", app["privacy"]), ("Terms of Service", app["terms"])])
    heading = f'{esc(app["name"])} guides &amp; help' if guides else f'{esc(app["name"])} help'
    sub = (esc(app["guides_intro"]) if guides and app.get("guides_intro") else
           "Step-by-step guides, plus support and the policies that cover the app." if guides
           else "Support and the policies that cover the app.")
    grid = f'<div class="sg-grid">\n{cards}\n</div>\n' if guides else ""
    # Old in-page anchors (e.g. drivemail.html#questions) that links elsewhere may still use.
    anchors = "".join(f'<span class="sg-anchor" id="{a}"></span>' for a in app.get("help_anchors", []))
    return (f'<section class="sg" id="{HELP_ID}" aria-labelledby="sg-h" style="--a:{app["accent"]}">{anchors}\n'
            f'<div class="sg-inner">\n<h2 class="sg-h" id="sg-h">{heading}</h2>\n<p class="sg-sub">{sub}</p>\n'
            f'{grid}<div class="sg-help">{links}</div>\n</div>\n</section>')


def crumbs_for(page, app):
    special = special_pages(app)
    trail = [(app["name"], app["home"])]
    if page in special:
        trail.append((special[page], None))
    else:
        g = {f: short for f, _, _, short in guides_of(app["id"])}
        trail += [("Guides", help_href(app)), (g.get(page) or page_meta(page)[0], None)]
    return trail


def render_breadcrumb(page, app):
    trail = crumbs_for(page, app)
    items = []
    for i, (name, href) in enumerate(trail):
        sep = '<span class="bc-sep" aria-hidden="true">&rsaquo;</span>' if i else ""
        body = f'<a href="{href}">{esc(name)}</a>' if href else f'<span aria-current="page">{esc(name)}</span>'
        items.append(f"<li>{sep}{body}</li>")
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": name, "item": url_of(href) if href else url_of(page)}
        for i, (name, href) in enumerate(trail, 1)]}
    return (f'<nav class="bc" aria-label="Breadcrumb" style="--a:{app["accent"]}"><ol>{"".join(items)}</ol></nav>\n'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def render_head(page, app, page_html):
    out = ['<link rel="stylesheet" href="site-chrome.css">', '<script src="site-chrome.js" defer></script>']
    if 'rel="icon"' not in page_html:             # several legal pages never had one
        if app is None:
            out.append(f'<link rel="icon" type="image/svg+xml" href="{HUB_ICON}">')
        else:
            out.append(f'<link rel="icon" type="image/png" href="{app["icon"]}">')
    return "\n".join(out)


# ---------------------------------------------------------------- hub

def render_hub():
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
        links = [("Guides", help_href(a) if guides_of(a["id"]) else None), ("Support", a["support"]),
                 ("Privacy", a["privacy"]), ("Terms", a["terms"])]
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
        "name": SITE["hub_title"], "url": BASE + HUB, "description": SITE["hub_description"],
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": a["name"], "url": url_of(a["home"])}
            for i, a in enumerate(APPS, 1)]},
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
<link rel="canonical" href="{BASE}{HUB}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(title)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{BASE}{HUB}">
<meta property="og:image" content="{BASE}{HUB_OG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}: {esc(', '.join(a['name'] for a in APPS))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}{HUB_OG}">
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
    <div class="hub-icons" aria-hidden="true">{''.join(f'<img src="{a["icon"]}" alt="" width="56" height="56">' for a in APPS)}</div>
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
FEATURES = re.compile(r'<section\b[^>]*\bid="features"[^>]*>.*?</section>', re.S)
CONTENT_OPEN = re.compile(r'<main\b[^>]*>|<div class="content">')


def empty(name): return f"{start(name)}\n{end(name)}"


def migrate(page, src, app):
    """Insert any marker blocks a page is missing (first run, or a newly added page)."""
    if start("site-header") not in src:
        src = APP_MENU.sub("\n", src)
        if len(OLD_NAV.findall(src)) != 1:
            sys.exit(f"build_chrome: {page}: expected exactly one old <nav><div class=\"nav-inner\"> to replace")
        src = OLD_NAV.sub(lambda m: empty("site-header"), src, count=1)
    if start("site-footer") not in src:
        if len(OLD_FOOTER.findall(src)) != 1:
            sys.exit(f"build_chrome: {page}: expected exactly one old <footer> to replace")
        src = OLD_FOOTER.sub(lambda m: empty("site-footer"), src, count=1)
    if start("site-head") not in src:
        src = src.replace("</head>", f"{empty('site-head')}\n</head>", 1)
    if app and page == home_file(app):
        if start("more-apps") not in src:
            src = src.replace(start("site-footer"), f"{empty('more-apps')}\n\n{start('site-footer')}", 1)
        if start("app-help") not in src:
            m = FEATURES.search(src)
            if m:   # right after the features section
                src = src[:m.end()] + f"\n\n{empty('app-help')}" + src[m.end():]
            else:   # no features section: just before "More apps"
                src = src.replace(start("more-apps"), f"{empty('app-help')}\n\n{start('more-apps')}", 1)
    elif app and start("breadcrumb") not in src:
        m = CONTENT_OPEN.search(src, src.find(end("site-header")))
        if not m:
            sys.exit(f"build_chrome: {page}: no <main> or <div class=\"content\"> to put the breadcrumb in")
        src = src[:m.end()] + f"\n{empty('breadcrumb')}" + src[m.end():]
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
    for name, render in (("more-apps", render_more), ("app-help", render_help), ("breadcrumb", render_breadcrumb)):
        if start(name) in src:
            src = fill(src, name, render(page, app))
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
        loc = url_of(page)
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
