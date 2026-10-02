#!/usr/bin/env python3
"""Generate the B2Gaudio + Digital Decks search landing pages.

Every product claim here is traceable to:
  B2Gaudio:      ~/Developer/B2Gaudio2/docs/marketing/00_FACTS_AND_CLAIMS.md (+ CLAUDE.md, source)
  Digital Decks: ~/Developer/Pricedex docs + source + the live App Store listing (v1.0.3)
"""
import html, json, pathlib, re

SITE = pathlib.Path(__file__).resolve().parent.parent
# Header, footer and favicon come from tools/build_chrome.py (data: tools/apps.json), which this
# script runs after writing the pages; render() only leaves the empty marker blocks for it to fill.

B2G_STORE = "https://apps.apple.com/us/app/b2gaudio/id6759938468"
DD_STORE = "https://apps.apple.com/us/app/digital-decks-card-scanner/id6794926765"

APPS = {
    "b2g": dict(
        name="B2Gaudio", store=B2G_STORE, app_id="6759938468", accent="#FF6B35", accent_dim="#CC5529",
        og_image="https://b2gaudio.com/og-image.png", icon="favicon.png",
        cta_top="Download B2Gaudio, free", cta_bottom="Get B2Gaudio on the App Store",
    ),
    "dd": dict(
        name="Digital Decks", store=DD_STORE, app_id="6794926765", accent="#2FA8FF", accent_dim="#1F8AD6",
        og_image=None, icon="digitaldecks-icon.png",
        cta_top="Get Digital Decks on the App Store", cta_bottom="Download Digital Decks",
    ),
}

CSS = """:root{--bg:#0A0A0F;--surface:#151520;--surface2:#1E1E2E;--accent:%(accent)s;--accent-dim:%(accent_dim)s;--text:#F5F5F7;--text2:#A1A1AA;--text3:#71717A;--border:#2A2A3A}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:12px 22px;border-radius:999px;font-weight:600}.btn:hover{background:var(--accent-dim);text-decoration:none}
main{max-width:820px;margin:0 auto;padding:120px 24px 40px}
h1{font-size:clamp(28px,5vw,44px);line-height:1.15;letter-spacing:-.02em;margin-bottom:16px}
.sub{color:var(--text2);font-size:1.15rem;margin-bottom:8px}
h2{font-size:1.6rem;margin:36px 0 12px;letter-spacing:-.01em}
p{margin-bottom:14px}
ul.plain{margin:0 0 14px 20px}ul.plain li{margin-bottom:6px}
.answer{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:14px;padding:24px;margin:24px 0}.answer p:last-child{margin-bottom:0}
.steps{display:grid;gap:14px;margin:18px 0}
.step{display:flex;gap:14px;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px}
.step .n{flex:0 0 auto;width:30px;height:30px;border-radius:50%%;background:var(--accent);color:#fff;font-weight:700;display:grid;place-items:center}
.step h3{font-size:1.05rem;margin-bottom:2px}.step p{color:var(--text2);margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:18px 0}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px}.card h3{font-size:1.05rem;margin-bottom:6px}.card p{color:var(--text2);font-size:.95rem;margin:0}
table{width:100%%;border-collapse:collapse;margin:18px 0;font-size:.95rem}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top}th{color:var(--text2);font-weight:600}
.faq h3{font-size:1.08rem;margin:22px 0 6px}.faq p{color:var(--text2)}
.cta-row{margin:26px 0}
.related{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}.related a{background:var(--surface);border:1px solid var(--border);border-radius:999px;padding:8px 14px;color:var(--text);font-size:.9rem}
"""


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def render(p):
    app = APPS[p["app"]]
    url = f"https://b2gaudio.com/{p['file']}"
    esc = lambda s: html.escape(s, quote=True)
    faq_ld = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": strip_tags(q),
             "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
            for q, a in p["faq"]
        ],
    }
    og_img = ""
    card = "summary"
    if not app["og_image"]:
        og_img = (f'<meta property="og:image" content="https://b2gaudio.com/{app["icon"]}">\n'
                  f'<meta name="twitter:image" content="https://b2gaudio.com/{app["icon"]}">\n')
    else:
        card = "summary_large_image"
        og_img = (f'<meta property="og:image" content="{app["og_image"]}">\n'
                  f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
                  f'<meta name="twitter:image" content="{app["og_image"]}">\n')
    related = "\n".join(f'    <a href="{h}">{t}</a>' for h, t in p["related"])
    faq_html = "\n".join(f"    <h3>{q}</h3>\n    <p>{a}</p>" for q, a in p["faq"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['title']}</title>
<meta name="description" content="{esc(p['desc'])}">
<link rel="canonical" href="{url}">
<meta name="apple-itunes-app" content="app-id={app['app_id']}">
<link rel="icon" type="image/png" href="{app['icon']}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{app['name']}">
<meta property="og:title" content="{esc(p['og_title'])}">
<meta property="og:description" content="{esc(p['desc'])}">
<meta property="og:url" content="{url}">
{og_img}<meta name="twitter:card" content="{card}">
<meta name="twitter:title" content="{esc(p['og_title'])}">
<meta name="twitter:description" content="{esc(p['desc'])}">
<style>
{CSS % app}
</style>
<script type="application/ld+json">
{json.dumps(faq_ld, ensure_ascii=False, indent=1)}
</script>
<!-- site-head:start -->
<!-- site-head:end -->
</head>
<body>
<!-- site-header:start -->
<!-- site-header:end -->
<main>
  <h1>{p['h1']}</h1>
  <p class="sub">{p['sub']}</p>
  <div class="answer">
{p['answer']}
    <p class="cta-row"><a class="btn" href="{app['store']}">{app['cta_top']}</a></p>
  </div>
{p['body']}
  <h2>Questions people ask</h2>
  <div class="faq">
{faq_html}
  </div>
  <p class="cta-row"><a class="btn" href="{app['store']}">{app['cta_bottom']}</a></p>
  <h2>Related guides</h2>
  <div class="related">
{related}
  </div>
</main>
<!-- site-footer:start -->
<!-- site-footer:end -->
</body>
</html>
"""


def steps(items):
    out = ['  <div class="steps">']
    for i, (h, t) in enumerate(items, 1):
        out.append(f'    <div class="step"><div class="n">{i}</div><div><h3>{h}</h3><p>{t}</p></div></div>')
    out.append("  </div>")
    return "\n".join(out)


def cards(items):
    out = ['  <div class="grid">']
    for h, t in items:
        out.append(f'    <div class="card"><h3>{h}</h3><p>{t}</p></div>')
    out.append("  </div>")
    return "\n".join(out)


def bullets(items):
    return '  <ul class="plain">\n' + "\n".join(f"    <li>{i}</li>" for i in items) + "\n  </ul>"


B2G_PAGES = [
    ("b2gaudio-sync-music-multiple-phones.html", "Play music on multiple phones"),
    ("b2gaudio-watch-movie-together-plane.html", "Watch a movie together on a plane"),
    ("b2gaudio-silent-disco-app.html", "Silent disco with phones"),
    ("b2gaudio-phones-as-party-speaker.html", "Phones as one party speaker"),
    ("b2gaudio-listen-to-audiobook-together.html", "Audiobooks together on a road trip"),
]
DD_PAGES = [
    ("digitaldecks-pokemon-card-scanner.html", "Pokémon card scanner"),
    ("digitaldecks-what-is-my-pokemon-card-worth.html", "What is my card worth?"),
    ("digitaldecks-pokemon-card-rarity-symbols.html", "Rarity symbols explained"),
    ("digitaldecks-build-deck-from-cards-you-own.html", "Build a deck from cards you own"),
    ("digitaldecks-pokemon-card-collection-tracker.html", "Collection tracker"),
]


def related_for(file, group, home, home_label):
    return [(f, t) for f, t in group if f != file] + [(home, home_label)]


# Shared B2Gaudio "what it doesn't do" list, straight from the never-claim section.
B2G_LIMITS = bullets([
    "iPhone and iPad only, iOS 17 or later. There is no Android version.",
    "Everyone has to be nearby, on the same WiFi network or within range for a direct peer-to-peer connection. It isn't for listening along with someone in another city.",
    "It doesn't use Bluetooth to connect the phones, and it has no AirPlay or CarPlay support.",
    "Apple Music tracks need each listener to have their own Apple Music subscription. Your own imported files, podcasts and audiobooks don't.",
])

pages = []

# ---------------------------------------------------------------- B2Gaudio
f = "b2gaudio-sync-music-multiple-phones.html"
pages.append(dict(
    app="b2g", file=f,
    title="How to Play Music on Multiple Phones at the Same Time — B2Gaudio",
    og_title="How to play music on multiple phones at the same time",
    desc="Want the same song playing on several iPhones at once, in sync? With B2Gaudio one iPhone hosts and every other iPhone or iPad joins over WiFi. Free, no account.",
    h1="How to play music on multiple phones at the same time",
    sub="The same song at the same moment on every iPhone in the room.",
    answer="""    <p><strong>Short answer:</strong> iPhone has no built-in way to play one song on several phones in sync, and pressing play on each phone by hand never lines up. <strong>B2Gaudio</strong> is a free iOS app built for exactly this. One iPhone hosts a session, everyone else opens the app and taps join, and every phone plays the same audio in time with the host over WiFi.</p>""",
    body="\n".join([
        "  <h2>How to set it up</h2>",
        steps([
            ("Install B2Gaudio on every phone", "It's free on iPhone and iPad (iOS 17 or later). No account, no sign-up."),
            ("Pick something to play on the host phone", "Music files you've imported, Apple Music, a podcast, an audiobook, or the soundtrack of a video."),
            ("Start a session", "The host phone makes the session visible to phones nearby."),
            ("Everyone else taps join", "Nearby phones see the session in the app. When the host plays, pauses, skips or seeks, every phone follows."),
        ]),
        "  <h2>How the phones stay together</h2>",
        "  <p>B2Gaudio doesn't use Bluetooth. The phones talk over WiFi: on the same network when there is one, or over Apple's peer-to-peer WiFi (the same kind of direct link AirDrop uses) when there isn't. Each joining phone measures how far its clock is from the host's, the host tells every phone exactly when to start, and while the track plays each phone keeps checking and nudges itself back in line.</p>",
        "  <h2>What you can play</h2>",
        cards([
            ("Your own music", "Import MP3s and other audio files from the Files app."),
            ("Apple Music", "Search and play Apple Music. Each listener needs their own subscription for Apple Music tracks."),
            ("Podcasts", "Search for a show or browse the Apple top charts."),
            ("Audiobooks", "Free public-domain books from LibriVox."),
            ("Video", "The host watches the video; every other phone plays its audio in sync."),
            ("Mixtapes", "Build playlists and share them with the group."),
        ]),
        "  <h2>What it doesn't do</h2>",
        B2G_LIMITS,
    ]),
    faq=[
        ("Can I play the same song on two iPhones at once?", "Yes, with an app made for it. In B2Gaudio one iPhone hosts a session and the other joins; both play the same track in sync over WiFi."),
        ("Does every phone need its own copy of the song?", "Not for music files you've imported, podcasts or audiobooks. The host sends the audio to the other phones. Apple Music is different: each listener needs their own Apple Music subscription to play Apple Music tracks."),
        ("Do the phones need internet?", "Not to stay in sync. The phones connect to each other over WiFi, or directly over Apple's peer-to-peer WiFi when there's no network. You only need internet for content that comes from the internet, like streaming Apple Music or downloading a podcast episode."),
        ("Does B2Gaudio use Bluetooth?", "No. The phones connect over WiFi and peer-to-peer WiFi, not Bluetooth."),
        ("Does it work on Android?", "No. B2Gaudio is for iPhone and iPad running iOS 17 or later."),
        ("How much does it cost?", "It's free. There's one non-personalized banner ad, no subscription, no in-app purchases and no tracking."),
    ],
    related=related_for(f, B2G_PAGES, "/", "B2Gaudio home"),
))

f = "b2gaudio-watch-movie-together-plane.html"
pages.append(dict(
    app="b2g", file=f,
    title="How to Watch a Movie Together on a Plane With Two Headphones — B2Gaudio",
    og_title="How to watch a movie together on a plane",
    desc="One screen, two people, two pairs of headphones. B2Gaudio plays a video on one iPhone or iPad and sends the audio to a second phone in sync, with no in-flight WiFi needed.",
    h1="How to watch a movie together on a plane",
    sub="One screen, two pairs of headphones, the same audio in both.",
    answer="""    <p><strong>Short answer:</strong> put the movie on one iPhone or iPad and send its sound to the second person's phone, so each of you listens through your own headphones. <strong>B2Gaudio</strong> does this: the host device plays the video, and a second iPhone joins the session and plays the audio in time with the picture. The two devices connect to each other directly, so you don't need to buy in-flight WiFi.</p>
    <p>iPhone and iPad also have a built-in Share Audio feature, but it only works with some AirPods and Beats headphones. B2Gaudio works with whatever headphones each person already uses with their own phone.</p>""",
    body="\n".join([
        "  <h2>How to set it up</h2>",
        steps([
            ("Before the flight: get the video onto the host device", "Install B2Gaudio on both devices, then import the video file into B2Gaudio from the Files app. Do this on the ground, while you still have internet."),
            ("On the plane: turn WiFi on", "Airplane mode lets you switch WiFi back on. You don't have to join the plane's network. B2Gaudio can connect the two devices over Apple's peer-to-peer WiFi."),
            ("Host starts a session and plays the video", "The video plays on the host's screen."),
            ("The second person taps join", "Their phone plays the movie's audio in sync with the host, through their own headphones."),
        ]),
        "  <h2>The picture stays on one screen</h2>",
        "  <p>B2Gaudio sends the audio, not the video. The joining phone doesn't show the movie, so plan to share the host's screen. An iPad propped on a tray table is the easy setup.</p>",
        "  <h2>What works and what doesn't</h2>",
        bullets([
            "Works with video files saved on the host device and imported from the Files app.",
            "It doesn't play video from streaming apps.",
            "Both people need an iPhone or iPad with iOS 17 or later, and both need B2Gaudio installed.",
            "It doesn't use Bluetooth or AirPlay to link the devices.",
            "Follow the crew's instructions on device use.",
        ]),
    ]),
    faq=[
        ("How can two people watch the same movie on a plane with separate headphones?", "Play the movie on one device and send its audio to the other person's phone. With B2Gaudio the host device plays the video and a second iPhone joins and plays the audio in sync through its own headphones."),
        ("Does it need in-flight WiFi?", "No. Turn WiFi on (airplane mode allows it) and B2Gaudio can connect the two devices directly over Apple's peer-to-peer WiFi. Load the video before you board."),
        ("Can the second phone show the movie too?", "No. B2Gaudio sends only the audio. You watch on the host's screen and each person hears it on their own device."),
        ("What videos can I use?", "Video files saved on the host device and imported from the Files app. It doesn't play video from streaming apps."),
        ("Can I just use a headphone splitter instead?", "If you both have wired headphones and a device with a headphone jack or adapter, a splitter works. B2Gaudio is for when each person has their own phone and headphones."),
    ],
    related=related_for(f, B2G_PAGES, "/", "B2Gaudio home"),
))

f = "b2gaudio-silent-disco-app.html"
pages.append(dict(
    app="b2g", file=f,
    title="Silent Disco App for iPhone: Use Phones and Headphones — B2Gaudio",
    og_title="A silent disco app that uses the phones you already have",
    desc="Throw a silent disco without renting headphones. B2Gaudio lets the DJ's iPhone host and every guest's iPhone play the same track in sync, into their own headphones. Free.",
    h1="A silent disco app that uses the phones you already have",
    sub="The DJ's phone hosts. Everyone else joins and dances with their own headphones.",
    answer="""    <p><strong>Short answer:</strong> a silent disco usually means renting wireless headphones and a transmitter. With <strong>B2Gaudio</strong>, the DJ's iPhone hosts a session and every guest's iPhone plays the same track in sync into their own headphones. It's free, there's no account, and it works over WiFi or, with no network around, directly between nearby phones.</p>""",
    body="\n".join([
        "  <h2>How to run one</h2>",
        steps([
            ("Everyone installs B2Gaudio", "Free on iPhone and iPad with iOS 17 or later. Send guests the link ahead of time."),
            ("The DJ builds a Mixtape", "Line up the set in a Mixtape (B2Gaudio's playlists) before people arrive."),
            ("Start the session", "Put everyone on the same WiFi network if there is one. With no network, nearby phones can still connect over Apple's peer-to-peer WiFi."),
            ("Guests tap join", "The DJ plays, pauses and skips, and every phone follows."),
        ]),
        "  <h2>Planning tips</h2>",
        bullets([
            "<strong>Use your own music files if you can.</strong> The host sends them to every phone. Apple Music tracks only play for guests who have their own Apple Music subscription.",
            "<strong>Guests bring their own headphones.</strong> Each phone plays through whatever is plugged into or paired with it.",
            "<strong>Charge up.</strong> Every phone is playing audio for the whole party.",
        ]),
        "  <h2>Limits worth knowing</h2>",
        bullets([
            "A session is one stream: everyone who joins hears what the host is playing.",
            "iPhone and iPad only. Guests with Android phones can't join.",
            "Everyone has to be nearby. This isn't a way to stream to people somewhere else.",
            "It doesn't use Bluetooth or AirPlay to connect the phones.",
        ]),
    ]),
    faq=[
        ("Can you do a silent disco with just phones and headphones?", "Yes, if everyone has an iPhone. With B2Gaudio one phone hosts and the rest join; every phone plays the same track in sync and each guest listens on their own headphones."),
        ("Do guests have to pay for anything?", "No. B2Gaudio is free. The only catch is Apple Music: guests need their own Apple Music subscription to hear Apple Music tracks. Music files the host imported play for everyone."),
        ("Does the DJ control playback for everyone?", "Yes. When the host plays, pauses, skips or seeks, every joined phone follows."),
        ("Does it work outside with no WiFi?", "Yes. When there's no shared network, nearby phones can connect directly over Apple's peer-to-peer WiFi."),
        ("Does it use Bluetooth?", "No. The phones connect over WiFi and peer-to-peer WiFi."),
    ],
    related=related_for(f, B2G_PAGES, "/", "B2Gaudio home"),
))

f = "b2gaudio-phones-as-party-speaker.html"
pages.append(dict(
    app="b2g", file=f,
    title="How to Use Multiple Phones as One Speaker for a Party — B2Gaudio",
    og_title="How to use several phones as one speaker",
    desc="Spread a few iPhones around the room and play the same song on all of them, in sync. B2Gaudio connects the phones over WiFi, no Bluetooth or extra speakers. Free.",
    h1="How to use several phones as one speaker",
    sub="Spread the phones around the room. Play one song on all of them at once.",
    answer="""    <p><strong>Short answer:</strong> set a few iPhones around the room and play the same song on every one of them in sync. <strong>B2Gaudio</strong> does the syncing: one phone hosts a session, the others join over WiFi, and they all play the host's music together instead of drifting apart the way phones started by hand do.</p>
    <p>Be realistic about volume. A phone speaker is small, so several phones spread out fill a room more evenly than one, but they won't match a proper party speaker.</p>""",
    body="\n".join([
        "  <h2>How to set it up</h2>",
        steps([
            ("Install B2Gaudio on each phone", "Free on iPhone and iPad with iOS 17 or later. Spare old iPhones and iPads count, as long as they run iOS 17."),
            ("Place the phones", "Spread them around the room rather than bunching them together."),
            ("Start a session on the host phone", "Choose music: your own files, Apple Music, podcasts or audiobooks."),
            ("Join from every other phone and turn the volume up", "The host controls play, pause and skip for all of them."),
        ]),
        "  <h2>Why phones started by hand don't work</h2>",
        "  <p>Press play on three phones at once and they're already apart, and they don't stay together. B2Gaudio gives every phone a shared start time and each phone keeps correcting its timing against the host while it plays.</p>",
        "  <h2>What it doesn't do</h2>",
        B2G_LIMITS,
    ]),
    faq=[
        ("Can I connect multiple phones to play the same music?", "Yes. With B2Gaudio one iPhone hosts and the others join over WiFi; they all play the same music in sync."),
        ("Can I use old iPhones or iPads as extra speakers?", "Yes, if they run iOS 17 or later. Every device just needs B2Gaudio installed."),
        ("Does it work with AirPlay or Bluetooth speakers?", "B2Gaudio doesn't support AirPlay, and it doesn't use Bluetooth to connect the phones. It's built around the phones' own WiFi."),
        ("Do I need internet?", "Not to connect the phones. You need it for internet content, like streaming Apple Music or downloading a podcast. Music files you've imported play without it."),
        ("Do all the phones need Apple Music?", "Only for Apple Music tracks, which need a subscription on each phone. Your own imported music files are sent from the host, so the other phones don't need a copy."),
    ],
    related=related_for(f, B2G_PAGES, "/", "B2Gaudio home"),
))

f = "b2gaudio-listen-to-audiobook-together.html"
pages.append(dict(
    app="b2g", file=f,
    title="How to Listen to an Audiobook Together on Multiple Phones (Road Trips) — B2Gaudio",
    og_title="How to listen to an audiobook or podcast together on several phones",
    desc="Listen to the same audiobook or podcast on several iPhones at once, in sync, each person with their own headphones. B2Gaudio plays free LibriVox audiobooks and podcasts.",
    h1="How to listen to an audiobook or podcast together on several phones",
    sub="Road trips, long drives, kids in the back seat: everyone on the same chapter.",
    answer="""    <p><strong>Short answer:</strong> have one phone host and the others play along in sync. With <strong>B2Gaudio</strong>, the host picks an audiobook or podcast episode and starts a session; every other iPhone or iPad joins and plays the same audio at the same moment, through its own headphones. It's free and has no account.</p>""",
    body="\n".join([
        "  <h2>How to set it up</h2>",
        steps([
            ("Install B2Gaudio on every phone", "Free on iPhone and iPad with iOS 17 or later."),
            ("Find something to listen to", "In the Library tab, open Browse, then Podcasts or Books. Search for a podcast or browse the top charts, or pick a free public-domain book from LibriVox."),
            ("Start a session and press play", "Play a chapter, or use Play from start for the whole book."),
            ("Everyone else taps join", "Pause for everybody at a rest stop, and pick up again together."),
        ]),
        "  <h2>What you can listen to</h2>",
        cards([
            ("Free audiobooks", "Public-domain classics from LibriVox."),
            ("Podcasts", "Search any show, or browse the Apple top charts."),
            ("Your own audio files", "DRM-free audiobook or music files imported from the Files app."),
        ]),
        "  <p>B2Gaudio can't play books from Audible or Apple Books.</p>",
        "  <h2>On the road</h2>",
        bullets([
            "The phones connect directly to each other over Apple's peer-to-peer WiFi, so you don't need a hotspot to keep them together.",
            "The host phone needs a data connection to download each episode or chapter. The other phones get the audio from the host.",
            "The first time you play a long chapter it can take a moment to prepare before it starts.",
            "There's no CarPlay app. B2Gaudio is for listening on the phones themselves.",
        ]),
    ]),
    faq=[
        ("Can two phones play the same audiobook at the same time?", "Yes. In B2Gaudio one phone hosts and the others join; they all play the same chapter in sync."),
        ("Does it work with Audible?", "No. B2Gaudio plays free LibriVox audiobooks, podcasts, and audio files you import yourself. It can't play Audible or Apple Books titles."),
        ("Does every phone need mobile data?", "No. The host downloads the episode or chapter and sends the audio to the other phones, which connect to it directly."),
        ("Can I use B2Gaudio with CarPlay?", "No. B2Gaudio has no CarPlay support. It's for passengers listening on their own phones and headphones."),
        ("Can everyone pause at once?", "Yes. When the host pauses, skips or seeks, every joined phone follows."),
    ],
    related=related_for(f, B2G_PAGES, "/", "B2Gaudio home"),
))

# ---------------------------------------------------------------- Digital Decks
DD_LIMITS = bullets([
    "English-language cards only. If it sees a Japanese, Korean or Chinese card it tells you, rather than guessing.",
    "Looking a card up needs an internet connection. Reading the number with the camera happens on the device.",
    "Prices are rough asking-price estimates, not appraisals, and brand-new cards may not have a price yet.",
    "It's an unofficial tool, not affiliated with or endorsed by any card publisher.",
])

f = "digitaldecks-pokemon-card-scanner.html"
pages.append(dict(
    app="dd", file=f,
    title="Pokémon Card Scanner App for iPhone and iPad — Digital Decks",
    og_title="A Pokémon card scanner app for iPhone and iPad",
    desc="Point your iPhone at a Pokémon card and Digital Decks reads its collector number, then shows the card, its set, rarity and a rough price. On-device reading, no ads, made for kids.",
    h1="A Pokémon card scanner app for iPhone and iPad",
    sub="Point the camera at the card. See what it is, how rare it is, and roughly what it's worth.",
    answer="""    <p><strong>Short answer:</strong> <strong>Digital Decks</strong> reads the small collector number printed at the bottom of a Pokémon card (like 4/102), looks the card up, and shows its name, artwork, set, rarity and a rough price. The camera reading runs on the device and no photo is saved or uploaded. It's built for kids: big buttons, read-aloud, no ads, no accounts.</p>""",
    body="\n".join([
        "  <h2>How scanning works</h2>",
        steps([
            ("Pick who's playing", "Each kid has a profile, so scanned cards go into the right collection."),
            ("Point the camera at the collector number", "The number is at the bottom of the card, for example 4/102 or 199/165."),
            ("Check the match and add it", "Tap Add to My Library. Scanning a whole stack? Turn on Add cards automatically."),
            ("Can't read the number? Search by name", "Type the card's name and pick it from the results."),
        ]),
        "  <p>A collector number on its own isn't unique, since many sets share the same numbers. Digital Decks also reads the card's name to narrow the match, and if it still isn't sure, it shows the options so you can tap the right one or skip it.</p>",
        "  <h2>What you see for each card</h2>",
        cards([
            ("Set and number", "Which set the card is from and where it sits in it."),
            ("Rarity in plain words", "How rare it is, with approximate pull odds a kid can follow."),
            ("Rough value", "An asking-price estimate for the version you own, plus typical asking prices for PSA 10 and CGC 10 copies."),
            ("Read aloud", "Tap the speaker to hear the card details."),
        ]),
        "  <h2>Good to know</h2>",
        DD_LIMITS,
    ]),
    faq=[
        ("Is there an app that scans Pokémon cards?", "Yes. Digital Decks for iPhone and iPad scans the collector number on a Pokémon card and shows the card, its set, rarity and a rough price."),
        ("How does it identify a card?", "It reads the collector number printed at the bottom of the card and the card's name, then looks the card up in a card database. If more than one card still matches, it asks you to pick."),
        ("Does it save or upload photos of my cards?", "No. The camera reading happens on the device and no photo is saved or uploaded."),
        ("Does it work on Japanese cards?", "No. The card databases it uses are English-only, so it flags Japanese, Korean and Chinese cards instead of matching them to the wrong card."),
        ("Does it grade my card?", "No. It shows what sellers are asking for PSA 10 and CGC 10 copies of that card, but it doesn't judge the condition of yours."),
        ("How much does it cost?", "It's a paid app on the App Store with no ads, no accounts and no subscription."),
    ],
    related=related_for(f, DD_PAGES, "digitaldecks.html", "Digital Decks home"),
))

f = "digitaldecks-what-is-my-pokemon-card-worth.html"
pages.append(dict(
    app="dd", file=f,
    title="What Is My Pokémon Card Worth? How to Check a Card's Value — Digital Decks",
    og_title="What is my Pokémon card worth?",
    desc="How to find out what a Pokémon card is worth: identify the exact card and version, compare real sales, and account for condition. Digital Decks gives a quick rough estimate.",
    h1="What is my Pokémon card worth?",
    sub="Identify the exact card first. Then look at what that exact version sells for.",
    answer="""    <p><strong>Short answer:</strong> a card's value depends on which exact card it is, which version (regular, holo, reverse holo), and its condition. Find the collector number at the bottom, match the version, then compare recent sales of that exact card. <strong>Digital Decks</strong> handles the first part by scanning the number, and shows a rough asking price for the version you pick, plus typical asking prices for graded PSA 10 and CGC 10 copies. Treat those as estimates, not an appraisal.</p>""",
    body="\n".join([
        "  <h2>How to check a card's value yourself</h2>",
        steps([
            ("Find the collector number", "It's printed at the bottom of the card, like 4/102. Name plus number plus set identifies the exact card."),
            ("Work out which version you have", "Regular, holo (shiny artwork) or reverse holo (shiny everywhere except the artwork). Different versions are worth different amounts."),
            ("Look at sold prices, not just asking prices", "An asking price is what a seller hopes to get. On eBay you can filter a search to sold items to see what cards actually went for."),
            ("Be honest about condition", "Scratches, bends and white wear on the edges lower the value. Graded cards sell differently from raw ones."),
        ]),
        "  <h2>What Digital Decks shows</h2>",
        bullets([
            "<strong>A raw price for your version.</strong> An asking-price figure from TCGplayer listings for the version you choose. When there's none, it uses the middle of the lowest eBay listings.",
            "<strong>PSA 10 and CGC 10.</strong> The median of up to five of the lowest eBay listings for a graded 10 of that card. These are asking prices, not sold prices.",
            "<strong>Collection value.</strong> A rough total for everything in the collection, counting copies.",
        ]),
        "  <p>What it doesn't do: account for your card's condition or check that it's genuine. Please don't use it to decide what to pay for, sell, or insure a card.</p>",
        "  <h2>Why a price might be missing</h2>",
        "  <p>Brand-new sets often don't have prices yet, so the app says the card is too new to price. The card databases behind the app are also sometimes unavailable, and a lookup can fail. Try again later.</p>",
    ]),
    faq=[
        ("How do I find out what my Pokémon card is worth?", "Identify the exact card from its collector number, work out the version (regular, holo or reverse holo), then compare recent sold prices for that exact card and version, adjusting for condition."),
        ("Why is the app's price different from what a card sold for?", "Digital Decks shows asking prices from current listings. Sellers usually ask more than cards actually sell for, and the app doesn't account for condition."),
        ("Are holo and reverse holo cards worth different amounts?", "Often, yes. That's why Digital Decks lets you pick the exact version you own before showing a price."),
        ("Does Digital Decks grade my card or predict a grade?", "No. It shows asking prices for PSA 10 and CGC 10 copies of the card, but it doesn't assess the condition of yours."),
        ("What does it mean if a card's number is higher than the set total?", "A number like 199/165 means the card is numbered past the regular set. These are often called secret rares."),
    ],
    related=related_for(f, DD_PAGES, "digitaldecks.html", "Digital Decks home"),
))

f = "digitaldecks-pokemon-card-rarity-symbols.html"
pages.append(dict(
    app="dd", file=f,
    title="Pokémon Card Rarity Symbols Explained: Circle, Diamond, Star — Digital Decks",
    og_title="How to tell a Pokémon card's rarity",
    desc="How to tell a Pokémon card's rarity from the symbol at the bottom: circle, diamond, star, and the black, silver and gold stars used in Scarlet & Violet sets.",
    h1="How to tell a Pokémon card's rarity",
    sub="Look at the small symbol at the bottom of the card, next to the collector number.",
    answer="""    <p><strong>Short answer:</strong> every modern Pokémon card has a rarity symbol at the bottom, next to its collector number. A <strong>circle</strong> means Common, a <strong>diamond</strong> means Uncommon, and a <strong>star</strong> means Rare. Scarlet &amp; Violet sets add more star symbols for the higher rarities, from two black stars up to three gold stars. If you'd rather not squint, <strong>Digital Decks</strong> scans the card and tells you its rarity in plain words.</p>""",
    body="\n".join([
        "  <h2>Rarity symbols in Scarlet &amp; Violet sets</h2>",
        """  <table>
    <tr><th>Symbol</th><th>Rarity</th></tr>
    <tr><td>Black circle</td><td>Common</td></tr>
    <tr><td>Black diamond</td><td>Uncommon</td></tr>
    <tr><td>One black star</td><td>Rare</td></tr>
    <tr><td>Two black stars</td><td>Double Rare</td></tr>
    <tr><td>One gold star</td><td>Illustration Rare</td></tr>
    <tr><td>Two silver stars</td><td>Ultra Rare</td></tr>
    <tr><td>Two gold stars</td><td>Special Illustration Rare</td></tr>
    <tr><td>Three gold stars</td><td>Hyper Rare</td></tr>
  </table>""",
        "  <p>Older sets use the circle, diamond and star, but not the multi-star symbols. Newer sets can introduce symbols of their own, so if you see one you don't recognize, look the card up.</p>",
        "  <h2>Other clues on the card</h2>",
        bullets([
            "<strong>A number higher than the set total.</strong> A card numbered 199/165 sits past the regular set. These are often called secret rares.",
            "<strong>Holo vs reverse holo.</strong> A holo card has shiny artwork. A reverse holo is shiny everywhere except the artwork. These are versions of a card, not rarity symbols, and they can be worth different amounts.",
            "<strong>1st Edition stamp.</strong> Some early cards carry a small 1st Edition stamp, which marks the first print run.",
        ]),
        "  <h2>Let the app read it for you</h2>",
        "  <p>Digital Decks reads the collector number, looks the card up, and shows its rarity in plain words with approximate pull odds, so a young collector can see why a card is special. The rarest pulls get a small celebration. Tap the speaker and it reads the details aloud.</p>",
    ]),
    faq=[
        ("What do the circle, diamond and star mean on Pokémon cards?", "Circle is Common, diamond is Uncommon, and star is Rare. The symbol is at the bottom of the card near the collector number."),
        ("What do gold stars mean on a Pokémon card?", "In Scarlet &amp; Violet sets, one gold star is an Illustration Rare, two gold stars a Special Illustration Rare, and three gold stars a Hyper Rare."),
        ("What do two black stars mean?", "Two black stars mark a Double Rare in Scarlet &amp; Violet sets."),
        ("Is a reverse holo a rarity?", "No. Reverse holo is a version of a card (shiny everywhere except the artwork), not a rarity. The rarity is still shown by the symbol."),
        ("What does it mean if the card number is bigger than the set number?", "A number like 199/165 means the card is numbered past the main set. Collectors often call these secret rares."),
    ],
    related=related_for(f, DD_PAGES, "digitaldecks.html", "Digital Decks home"),
))

f = "digitaldecks-build-deck-from-cards-you-own.html"
pages.append(dict(
    app="dd", file=f,
    title="How to Build a Pokémon Deck From the Cards You Own — Digital Decks",
    og_title="How to build a Pokémon deck from cards you already own",
    desc="Build a legal 60-card Pokémon deck from the cards you already have: pick a type, keep evolution lines together, add Trainers and match Energy. Digital Decks does it for you.",
    h1="How to build a Pokémon deck from cards you already own",
    sub="Pick a type, build around your best attacker, and fill out 60 cards with what's in the box.",
    answer="""    <p><strong>Short answer:</strong> a Pokémon deck is exactly 60 cards, with no more than 4 copies of any card with the same name (Basic Energy doesn't count) and at least one Basic Pokémon. Pick one or two types, build around an attacker and its whole evolution line, add Trainers that draw and search, then add enough Energy to pay for your attacks. <strong>Digital Decks</strong> does this automatically from the cards your child has scanned, rates the deck out of five stars, and lists the cards that would make it better.</p>""",
    body="\n".join([
        "  <h2>The deck-building rules</h2>",
        bullets([
            "Exactly 60 cards.",
            "No more than 4 copies of a card with the same name. Basic Energy is the exception.",
            "At least one Basic Pokémon, or you can't start the game.",
            "Evolutions need the stage before them in play. Rare Candy is the exception: it lets a Basic Pokémon evolve straight into its Stage 2.",
            "When you play: one Supporter per turn, as many Items as you like, and only one Stadium in play at a time.",
        ]),
        "  <h2>Building it by hand</h2>",
        steps([
            ("Sort the cards by type", "Fire, Water, Grass and so on. One or two types keeps the Energy simple."),
            ("Choose a main attacker and its whole line", "If your attacker evolves, include the Basic and Stage 1 too, with more copies of the lower stages."),
            ("Add Trainers", "Supporters that draw cards, Items that search for Pokémon, and Rare Candy if you're running a Stage 2."),
            ("Add Energy to match the attacks", "Count what your attackers need and pack enough of that Energy type."),
            ("Count to 60", "Trim anything over 4 copies. If you're short, note what's missing."),
        ]),
        "  <h2>How Digital Decks builds it</h2>",
        bullets([
            "Pick one or two types and it builds the strongest deck it can from cards the child actually owns. It never adds a card they don't have.",
            "Evolution lines stay together, and Energy is matched to what the attackers cost.",
            "Support cards are chosen by what they do, so the deck keeps room for search cards, Rare Candy and a Stadium.",
            "Every deck gets a 1 to 5 star rating and a list of cards to look for. If the collection is short of 60, it says how many more cards are needed.",
            "It explains how to play the deck in plain language, and only mentions cards that are really in it.",
            "Save decks with a name, and choose to use each card in only one deck.",
        ]),
        "  <p>It follows the deck-building rules above. It doesn't check which cards are currently allowed in tournament Standard format.</p>",
    ]),
    faq=[
        ("How many cards are in a Pokémon deck?", "Exactly 60, with no more than 4 copies of any card with the same name, except Basic Energy."),
        ("How many Energy cards should a deck have?", "Enough to pay for your attackers' attacks. Count what they cost and pack that type of Energy to match. Digital Decks works this out from the attacks on the cards you own."),
        ("What is Rare Candy for?", "Rare Candy lets a Basic Pokémon evolve straight into its Stage 2, so your biggest attacker can arrive a turn sooner."),
        ("Can I build a deck if I don't have 60 cards?", "Digital Decks will build the best deck it can and tell you how many more cards you need, plus which ones would help most."),
        ("Is the deck tournament legal?", "It follows the deck-building rules (60 cards, 4-copy limit, Basic Pokémon, complete evolution lines). It doesn't check which sets are currently legal in Standard format."),
    ],
    related=related_for(f, DD_PAGES, "digitaldecks.html", "Digital Decks home"),
))

f = "digitaldecks-pokemon-card-collection-tracker.html"
pages.append(dict(
    app="dd", file=f,
    title="Pokémon Card Collection Tracker App for Kids — Digital Decks",
    og_title="A Pokémon card collection tracker for kids",
    desc="Track a Pokémon card collection on iPhone or iPad: scan cards in, count copies, filter by type, set or rarity, and see a rough total value. A separate profile for each kid.",
    h1="A Pokémon card collection tracker for kids",
    sub="Scan the shoebox once. Know what you have, how many, and roughly what it's worth.",
    answer="""    <p><strong>Short answer:</strong> <strong>Digital Decks</strong> turns scanned cards into a digital collection. It tracks every card and how many copies you have, filters by type, set or rarity, and shows a rough total value. Each child gets their own profile so nobody can change anybody else's cards. There's no account, and the collection stays on the device.</p>""",
    body="\n".join([
        "  <h2>How to track a collection</h2>",
        steps([
            ("Make a profile for each kid", "A name, a picture and a colour. Their cards and decks stay separate."),
            ("Scan cards in", "Point the camera at the collector number. For a big stack, turn on Add cards automatically."),
            ("Pick the exact version", "Regular, holo or reverse holo, so the value matches the card you actually have."),
            ("Adjust copies", "Tap a card to open it and use the big plus and minus buttons."),
        ]),
        "  <h2>Finding things in the collection</h2>",
        cards([
            ("Filter", "By type, set or rarity."),
            ("Search", "Find a card by name."),
            ("Total value", "A rough estimate for the whole collection, counting copies."),
            ("Build decks", "Turn the collection into a playable deck with the deck builder."),
        ]),
        "  <h2>Privacy and where the data lives</h2>",
        bullets([
            "No accounts, no ads, no analytics, no chat.",
            "The collection is stored on the device. There's no cloud sync, so a collection lives on the iPhone or iPad where it was scanned.",
            "The one link out of the app sits behind a parental gate.",
        ]),
    ]),
    faq=[
        ("What's the easiest way to keep track of a Pokémon card collection?", "Scan the cards into an app that counts copies for you. Digital Decks reads each card's collector number, adds it to the collection, and keeps a count of duplicates."),
        ("Can two kids use the same iPad?", "Yes. Each child gets their own profile with a separate collection and deck list, and neither can change the other's cards."),
        ("Does the collection sync between devices?", "No. There's no account and no cloud sync. The collection stays on the device where it was scanned."),
        ("How is the total value worked out?", "It adds up rough asking-price estimates for each card, counting copies. It's a ballpark figure, not an appraisal, and cards without a price yet can't add to it."),
        ("Can it track Japanese cards?", "No. Digital Decks works with English-language cards."),
    ],
    related=related_for(f, DD_PAGES, "digitaldecks.html", "Digital Decks home"),
))

for p in pages:
    (SITE / p["file"]).write_text(render(p))
    print("wrote", p["file"])

# Fill in the shared header/footer and re-apply App Store campaign tags (render() emits neither).
import subprocess, sys
subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("build_chrome.py"))], check=True)
