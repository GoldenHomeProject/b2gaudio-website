/* Progressive enhancement for the shared header. Navigation works without this file:
   the Apps dropdown and the phone menu are <details> elements. This only adds the
   behaviour <details> lacks: one menu open at a time, close on outside click, close on Escape. */
(function () {
    var menus = document.querySelectorAll('.sh details');
    if (!menus.length) return;
    function closeAll(except) {
        menus.forEach(function (d) { if (d !== except) d.open = false; });
    }
    menus.forEach(function (d) {
        d.addEventListener('toggle', function () { if (d.open) closeAll(d); });
    });
    document.addEventListener('click', function (e) {
        menus.forEach(function (d) { if (d.open && !d.contains(e.target)) d.open = false; });
    });
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        menus.forEach(function (d) {
            if (d.open) { d.open = false; var s = d.querySelector('summary'); if (s) s.focus(); }
        });
    });
    // Following an in-page link from the phone menu (e.g. Guides on the app's own page)
    // should not leave the menu covering the section it just scrolled to.
    document.querySelectorAll('.sh-menu-panel a').forEach(function (a) {
        a.addEventListener('click', function () { closeAll(null); });
    });
})();
