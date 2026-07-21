// Header collapse + sidebar toggle for the hub page.
// Elements are queried fresh on every event (rather than cached) since Dash
// re-renders #page-content on route changes and would otherwise leave us
// holding stale references to removed nodes.

window.addEventListener('scroll', function () {
    var header = document.getElementById('site-header');
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 40);
});

document.addEventListener('click', function (event) {
    var sidebar = document.getElementById('nav-sidebar');
    var toggleBtn = document.getElementById('nav-toggle-btn');
    if (!sidebar || !toggleBtn) return;

    if (event.target.closest('#nav-toggle-btn')) {
        sidebar.classList.toggle('open');
        toggleBtn.classList.toggle('active');
        return;
    }

    // Click outside the open sidebar closes it.
    if (sidebar.classList.contains('open') && !event.target.closest('#nav-sidebar')) {
        sidebar.classList.remove('open');
        toggleBtn.classList.remove('active');
    }
});

document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    var sidebar = document.getElementById('nav-sidebar');
    var toggleBtn = document.getElementById('nav-toggle-btn');
    if (!sidebar) return;
    sidebar.classList.remove('open');
    if (toggleBtn) toggleBtn.classList.remove('active');
});
