# OG image builder

`b2gaudio-og.html` renders the 1200x630 social card at `/og-image.png`.

Re-render after editing:

    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
      --screenshot="$PWD/og-image.png" --window-size=1200,630 \
      "file://$PWD/og-builder/b2gaudio-og.html"

Then commit `og-image.png`. Facebook and LinkedIn cache aggressively; use their
sharing debuggers to force a re-scrape after changing the art.

`apps-og.html` renders `/og-apps.png`, the card for the `/apps.html` hub. Re-render it
the same way (swap the two file names) when an app is added or changes its icon.

The pages in this folder are internal tools. They are publicly reachable on GitHub Pages,
so each one carries `<meta name="robots" content="noindex, nofollow">`, and
`tools/build_chrome.py` never adds them to `sitemap.xml`.
