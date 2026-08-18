document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('menuToggle');
  var nav = document.getElementById('mobileNav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }
});
