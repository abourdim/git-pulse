/* GitPulse — UI interactions */

document.addEventListener("DOMContentLoaded", function () {
  setupSidebar();
  highlightActiveLink();
});

/* ── Sidebar toggle (mobile) ── */
function setupSidebar() {
  var hamburger = document.getElementById("hamburger");
  var sidebar   = document.getElementById("sidebar");
  var overlay   = document.getElementById("sidebarOverlay");

  if (!hamburger || !sidebar) return;

  hamburger.addEventListener("click", function () {
    sidebar.classList.toggle("open");
    if (overlay) overlay.classList.toggle("visible");
  });

  if (overlay) {
    overlay.addEventListener("click", function () {
      sidebar.classList.remove("open");
      overlay.classList.remove("visible");
    });
  }

  // Close sidebar on link click (mobile)
  var links = sidebar.querySelectorAll(".sb-link");
  for (var i = 0; i < links.length; i++) {
    links[i].addEventListener("click", function () {
      if (window.innerWidth <= 860) {
        sidebar.classList.remove("open");
        if (overlay) overlay.classList.remove("visible");
      }
    });
  }
}

/* ── Highlight current page in sidebar ── */
function highlightActiveLink() {
  var path = window.location.pathname;
  var links = document.querySelectorAll(".sb-link");

  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute("href");
    if (!href) continue;

    // Exact match for root, startsWith for others
    if (path === "/" && href === "/") {
      links[i].classList.add("active");
    } else if (href !== "/" && path.indexOf(href) === 0) {
      links[i].classList.add("active");
    }
  }
}
