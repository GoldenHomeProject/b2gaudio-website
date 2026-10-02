# Site tools

b2gaudio.com is plain static HTML served by GitHub Pages from `main`. Every page shares one
header and one footer, written into the page by a script from one data file, so the navigation
is the same everywhere and a new app shows up on every page at once.

The chrome is deliberately unbranded: the header starts with a neutral "All apps" link (grid icon)
to the `apps.html` hub ("Our Apps"), with a caret beside it for a quick app switcher. The only
company name on the site is the legal copyright line in the footer (`site.copyright`).

| File | What it is |
| --- | --- |
| `tools/apps.json` | The list of apps (name, icon, accent colour, status, links, App Store id) and site-wide settings (hub title and description, contact email, copyright line). |
| `tools/build_chrome.py` | Writes the header, footer and favicon into every page, adds the "More apps from us" strip to each app's home page, regenerates `apps.html` (the hub) and `sitemap.xml`, and tags App Store links. Safe to run any time; a second run changes nothing. |
| `og-builder/apps-og.html` | Source of `og-apps.png`, the hub's 1200x630 social card (see `og-builder/README.md`). |
| `site-chrome.css`, `site-chrome.js` | Styles for the shared chrome; the JS only adds niceties (Escape / outside click closes menus). Menus are `<details>`, so navigation works with JS off. |
| `tools/gen_guides.py` | Generates the B2Gaudio and Digital Decks guide pages, then runs `build_chrome.py`. |
| `tools/tag_store_links.py` | Adds the App Store Connect campaign (`pt`, `ct=web-<page>`) to every App Store link. `build_chrome.py` already does this for what it writes; run this after hand-editing a page. |

The generated parts of a page sit between markers. Don't edit inside them, it will be overwritten:
`<!-- site-head:start/end -->`, `<!-- site-header:start/end -->`, `<!-- site-footer:start/end -->`,
`<!-- more-apps:start/end -->`. Everything outside the markers is the page's own and is never touched.

## Adding a new app

1. Add the app's icon at the site root (a square PNG, 192 px is plenty), e.g. `newapp-icon.png`.
2. Create its pages at the site root, using an existing app's pages as a template:
   `newapp.html` (home), `newapp-support.html`, `newapp-privacy.html`, `newapp-terms.html`.
   Each page needs the marker pairs in place of a header/footer: put `<!-- site-head:start -->`
   and `<!-- site-head:end -->` just before `</head>`, `<!-- site-header:start -->` /
   `<!-- site-header:end -->` straight after `<body>`, and `<!-- site-footer:start -->` /
   `<!-- site-footer:end -->` just before `</body>`. Leave room at the top of the page for the
   fixed 64 px header (the existing pages use about 120 px of top padding).
   On the home page, give the guides section `id="guides"` if it has one.
3. Add an entry to `apps` in `tools/apps.json`:
   ```json
   {
     "id": "newapp", "name": "New App", "icon": "newapp-icon.png",
     "accent": "#7A5CFF", "accent_text": "#FFFFFF",
     "status": "coming_soon",
     "tagline": "Short line, copied from the app's own page.",
     "summary": "One or two sentences, copied from the app's own page.",
     "platform": "iPhone",
     "home": "newapp.html", "guides": null,
     "support": "newapp-support.html", "privacy": "newapp-privacy.html", "terms": "newapp-terms.html",
     "app_store_id": "1234567890",
     "pages": ["newapp.html", "newapp-*.html"]
   }
   ```
   `status` is `"live"` or `"coming_soon"`. Coming-soon apps get a "Coming soon" label and no App
   Store button anywhere. `guides` is a link like `"newapp.html#guides"`, or `null` for none.
   `pages` are filename globs; every page must match exactly one app (the script stops if not).
   `accent_text` is the text colour used on the accent-coloured button; pick whichever of white or
   a dark shade of the accent is readable.
4. Run `python3 tools/build_chrome.py`. The app now appears in every page's app switcher and footer,
   on `apps.html`, in the "More apps from us" strip on the other apps' home pages, and its pages are
   in `sitemap.xml`.
5. Add its icon to `og-builder/apps-og.html` and re-render `og-apps.png` (see `og-builder/README.md`).
6. Look at it: `python3 -m http.server 8765` and open `http://127.0.0.1:8765/apps.html` at phone and
   desktop widths.
7. When it goes live on the App Store, change `status` to `"live"` and run the script again.
8. Commit and push `main`; GitHub Pages deploys it.

Rules that keep App Store Connect, AdMob and search happy: never rename or delete an existing page
(App Store listings point at the privacy, support and marketing URLs), keep `app-ads.txt`, `CNAME`,
`robots.txt` and the `google*.html` verification file, and only use copy that is already true on the
app's own page.
