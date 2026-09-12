(function () {
  "use strict";

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("mainnav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Cookie notice (essential cookies only - stored per browser)
  var banner = document.getElementById("cookie-banner");
  var accept = document.getElementById("cookie-accept");
  if (banner && accept) {
    var seen = false;
    try { seen = localStorage.getItem("va_cookie_notice") === "1"; } catch (e) {}
    if (!seen) banner.hidden = false;
    accept.addEventListener("click", function () {
      banner.hidden = true;
      try { localStorage.setItem("va_cookie_notice", "1"); } catch (e) {}
    });
  }

  // Product gallery thumbnails
  var mainImg = document.querySelector("[data-gallery-main]");
  document.querySelectorAll("[data-gallery-thumb]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (!mainImg) return;
      mainImg.src = btn.getAttribute("data-gallery-thumb");
      document.querySelectorAll("[data-gallery-thumb]").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
    });
  });

  // Quantity steppers
  document.querySelectorAll("[data-qty]").forEach(function (wrap) {
    var input = wrap.querySelector("input");
    wrap.querySelectorAll("button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var v = parseInt(input.value || "1", 10);
        v += btn.getAttribute("data-step") === "up" ? 1 : -1;
        input.value = Math.max(1, Math.min(99, v));
      });
    });
  });

  // Checkout: hide address when collecting from office
  var deliveryRadios = document.querySelectorAll("input[name=delivery_method]");
  var addressBlock = document.getElementById("address-block");
  function syncAddress() {
    var val = document.querySelector("input[name=delivery_method]:checked");
    if (addressBlock) addressBlock.hidden = !!(val && val.value === "pickup");
  }
  deliveryRadios.forEach(function (r) { r.addEventListener("change", syncAddress); });
  if (deliveryRadios.length) syncAddress();

  // Auto-submit selects (sort dropdown)
  document.querySelectorAll("[data-autosubmit]").forEach(function (el) {
    el.addEventListener("change", function () { el.form && el.form.submit(); });
  });

  // Auto-hide alerts
  document.querySelectorAll(".alert-success, .alert-info").forEach(function (el) {
    setTimeout(function () { el.style.transition = "opacity .5s"; el.style.opacity = "0"; }, 6000);
  });
})();
