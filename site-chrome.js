/* Progressive enhancement for the shared header. Navigation works without this file:
   the app tabs are plain links in a strip that scrolls sideways, and "More" is a <details>.
   This only (1) scrolls the current app's tab into view on narrow screens and
   (2) closes the "More" panel on an outside click or Escape. */
(function () {
    var strip = document.querySelector('.sh-strip');
    var cur = strip && strip.querySelector('.sh-tab.is-current');
    if (strip && cur && strip.scrollWidth > strip.clientWidth) {
        // Scroll only as far as needed to show the current tab clear of the right-edge fade,
        // so the tabs before it (and "All apps") stay in view whenever they can.
        var s = strip.getBoundingClientRect(), c = cur.getBoundingClientRect(), fade = 36;
        if (c.right > s.right - fade) strip.scrollLeft += c.right - (s.right - fade);
    }
    if (strip) {   // fade the left edge too once tabs have scrolled off it
        var mark = function () { strip.toggleAttribute('data-scrolled', strip.scrollLeft > 4); };
        strip.addEventListener('scroll', mark, { passive: true });
        mark();
    }
    var more = document.querySelector('.sh-more');
    if (!more) return;
    document.addEventListener('click', function (e) {
        if (more.open && !more.contains(e.target)) more.open = false;
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && more.open) { more.open = false; more.querySelector('summary').focus(); }
    });
})();
