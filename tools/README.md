# Site tools

b2gaudio.com is plain static HTML served by GitHub Pages from `main`. Every page shares one
header and one footer, written into the page by a script from one data file, so the navigation
is the same everywhere and a new app shows up on every page at once.

**How a visitor gets around**
- **Header (every page):** one row of tabs, "All apps" (to the `apps.html` hub, "Our Apps") then every
  app by icon and name, in `apps.json` order. The current app's tab is underlined in its colour, and its
  "Get the app" button sits on the right ("Coming soon" for an app that isn't live). On phones the tabs
  use short names and scroll sideways. More than six apps: the rest go under a "More" menu.
- **App home pages:** a generated "Guides & help" section (right after the features section) lists every
  guide page of that app, plus Support, Privacy Policy and Terms of Service.
- **Every other app page** (guides, support, privacy, terms): a breadcrumb at the top of the content,
  e.g. "DriveMail Voice › Guides › Gmail on CarPlay", plus a separate BreadcrumbList JSON-LD block.
- **Footer (every page):** every app's guides, support, privacy and terms, contact, copyright.

The chrome is deliberately unbranded. The only company name on the site is the legal copyright line in
the footer (`site.copyright`).

| File | What it is |
| --- | --- |
| `tools/apps.json` | The list of apps (name, short name, icon, accent colour, status, links, App Store id) and site-wide settings (hub title and description, contact email, copyright line). Order = header tab order. |
| `tools/build_chrome.py` | Writes all the generated blocks below into every page, regenerates `apps.html` (the hub) and `sitemap.xml`, and tags App Store links. Safe to run any time; a second run changes nothing. |
| `site-chrome.css`, `site-chrome.js` | Styles for everything generated. The JS only scrolls the current tab into view on phones and closes "More" on Escape; navigation works with JS off. |
| `og-builder/apps-og.html` | Source of `og-apps.png`, the hub's 1200x630 social card (see `og-builder/README.md`). |
| `tools/gen_guides.py` | Generates the B2Gaudio and Digital Decks guide pages, then runs `build_chrome.py`. |
| `tools/tag_store_links.py` | Adds the App Store Connect campaign (`pt`, `ct=web-<page>`) to every App Store link. `build_chrome.py` already does this for what it writes; run this after hand-editing a page. |

The generated parts of a page sit between markers. Don't edit inside them, it will be overwritten:
`site-head`, `site-header`, `site-footer` (every page), `app-help` and `more-apps` (app home pages),
`breadcrumb` (other app pages), each as `<!-- name:start -->` … `<!-- name:end -->`. The script adds any
missing ones itself. Everything outside the markers is the page's own and is never touched.

**Guides are found, not listed.** Any page matching an app's `pages` globs that isn't its home, support,
privacy or terms page is a guide. Its title is the page's `<h1>`, its one-liner is the first sentence of
its meta description. Optional per-app settings in `apps.json`: `guides` (a list of
`[file, short label]` that fixes the order and gives each guide its short breadcrumb label; unlisted
guides go last, labelled by their `<h1>`), `guides_intro` (the line under the section heading) and
`help_anchors` (old in-page anchors such as `drivemail.html#questions` that should keep landing on the
section). So to add a guide: create the page (with `<h1>`, meta description, and a `<main>` or
`<div class="content">` for the breadcrumb to go in), optionally add it to that app's `guides` list,
then run `python3 tools/build_chrome.py`.

## Adding a new app

1. Add the app's icon at the site root (a square PNG, 192 px is plenty), e.g. `newapp-icon.png`.
2. Create its pages at the site root, using an existing app's pages as a template:
   `newapp.html` (home), `newapp-support.html`, `newapp-privacy.html`, `newapp-terms.html`, plus any
   guides as `newapp-<topic>.html`. Each page needs the marker pairs in place of a header/footer: put
   `<!-- site-head:start -->` and `<!-- site-head:end -->` just before `</head>`,
   `<!-- site-header:start -->` / `<!-- site-header:end -->` straight after `<body>`, and
   `<!-- site-footer:start -->` / `<!-- site-footer:end -->` just before `</body>`. Leave room at the top
   of the page for the fixed 64 px header (the existing pages use about 120 px of top padding). Wrap
   each non-home page's content in `<main>` or `<div class="content">`.
3. Add an entry to `apps` in `tools/apps.json`, where you want its header tab to appear:
   ```json
   {
     "id": "newapp", "name": "New App", "short": "New App", "icon": "newapp-icon.png",
     "accent": "#7A5CFF", "accent_text": "#FFFFFF",
     "status": "coming_soon",
     "tagline": "Short line, copied from the app's own page.",
     "summary": "One or two sentences, copied from the app's own page.",
     "platform": "iPhone",
     "home": "newapp.html",
     "support": "newapp-support.html", "privacy": "newapp-privacy.html", "terms": "newapp-terms.html",
     "app_store_id": "1234567890",
     "pages": ["newapp.html", "newapp-*.html"]
   }
   ```
   `status` is `"live"` or `"coming_soon"`. Coming-soon apps get a "Soon" label and no App Store button
   anywhere. `short` is the tab label on phones (keep it to about 10 characters). `pages` are filename
   globs; every page must match exactly one app (the script stops if not). `accent_text` is the text
   colour on the accent-coloured button; pick whichever of white or a dark shade of the accent is readable.
4. Run `python3 tools/build_chrome.py`. The app now has a header tab on every page, a footer column, a
   card on `apps.html`, a place in the other apps' "More apps from us", a "Guides & help" section on its
   home page, breadcrumbs on its other pages, and its pages are in `sitemap.xml`.
5. Add its icon to `og-builder/apps-og.html` and re-render `og-apps.png` (see `og-builder/README.md`).
6. Look at it: `python3 -m http.server 8765` and open `http://127.0.0.1:8765/apps.html` at phone and
   desktop widths.
7. When it goes live on the App Store, change `status` to `"live"` and run the script again.
8. Commit and push `main`; GitHub Pages deploys it.

Rules that keep App Store Connect, AdMob and search happy: never rename or delete an existing page
(App Store listings point at the privacy, support and marketing URLs), keep `app-ads.txt`, `CNAME`,
`robots.txt` and the `google*.html` verification file, and only use copy that is already true on the
app's own page.
