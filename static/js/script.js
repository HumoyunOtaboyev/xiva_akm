"use strict";

// ---- Mobile menu ----
const menuBtn = document.querySelector("#menu");
const navLinks = document.querySelector("#nav-links");

if (menuBtn && navLinks) {
  const setMenu = (open) => {
    navLinks.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    menuBtn.setAttribute("aria-label", open ? "Menyuni yopish" : "Menyuni ochish");
  };

  menuBtn.addEventListener("click", () => {
    setMenu(!navLinks.classList.contains("open"));
  });

  // Close the menu after navigating (mobile)
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMenu(false));
  });
}

// ---- Header shadow on scroll (rAF-throttled, no inline style writes) ----
const header = document.querySelector("header");
if (header) {
  let ticking = false;
  const update = () => {
    header.classList.toggle("scrolled", window.scrollY > 50);
    ticking = false;
  };
  window.addEventListener(
    "scroll",
    () => {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    },
    { passive: true }
  );
  update();
}

// ---- Reveal-on-scroll (animate once, then stop observing) ----
const animated = document.querySelectorAll(".scroll-animate");
if ("IntersectionObserver" in window && animated.length) {
  const io = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );
  animated.forEach((el) => io.observe(el));
} else {
  // No IO support → show everything
  animated.forEach((el) => el.classList.add("animate"));
}
