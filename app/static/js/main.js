/* BuyZenix main.js */
(function () {
  /* Header scroll effect */
  var header = document.getElementById('siteHeader');
  if (header) {
    window.addEventListener('scroll', function () {
      header.classList.toggle('scrolled', window.scrollY > 60);
    });
  }

  /* Mobile menu toggle */
  var toggle = document.getElementById('mobileToggle');
  var menu = document.getElementById('mobileMenu');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      menu.classList.toggle('active');
      toggle.textContent = menu.classList.contains('active') ? '✕' : '☰';
    });
    /* Close menu on link click */
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        menu.classList.remove('active');
        toggle.textContent = '☰';
      });
    });
  }

  /* Close mobile menu on resize to desktop */
  window.addEventListener('resize', function () {
    if (window.innerWidth > 860 && menu && menu.classList.contains('active')) {
      menu.classList.remove('active');
      toggle.textContent = '☰';
    }
  });
})();
