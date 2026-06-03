# Frontend Modernization & Optimization — Design

**Date:** 2026-06-03
**Project:** xiva_akm — Xiva shahar Axborot-Kutubxona Markazi (Django SSR site)
**Status:** Approved (scoping + visual choices confirmed by owner)

## Goal
Full UI/UX review + fix of the production frontend, plus performance optimization. Django server-rendered templates, vanilla CSS/JS (no JS framework).

## Approved decisions
- **CSS strategy:** custom CSS, no framework. Remove all reliance on Bootstrap class names (Bootstrap was never loaded — large parts of the UI render unstyled in production).
- **Visual direction:** modernize with a cohesive design system.
- **Palette:** *Heritage Khiva* — turquoise primary, terracotta accent, cream surface.
  - `--primary #0E7C86`, `--accent #E07A3F`, `--surface #FBFAF7`, `--text #1C2B2D`, `--muted #5C6B6D`, `--border #E5E0D8`.
- **Icons:** remove Font Awesome CDN; use inline SVG sprite (UI + brand icons).
- **Backend:** include critical, safe, env-driven fixes.

## Critical issues being fixed
1. Bootstrap classes used but Bootstrap not loaded → rewrite 5 templates to semantic custom classes.
2. `script.js` `querySelector("#")` SyntaxError on `href="#"` links → guard.
3. `DEBUG = True` in production → env-driven, default False.

## Work breakdown
1. **Design system CSS** — token layer (CSS vars), base, layout, semantic components, minimal utility layer. Two files: `style.css` (core), `custom.css` (utilities). Fixed-header offset via `body padding-top` (removes per-page margin hacks; fixes content hidden behind sticky header on hodimlar/news).
2. **base.html** — drop Font Awesome; add meta description, favicon, `theme-color`, Open Graph/Twitter; include SVG sprite.
3. **Inline SVG sprite** — `templates/components/icons.html` with `<symbol>` defs; `<use>` at call sites.
4. **header.html** — accessible mobile nav (`aria-label`, `aria-expanded`), SVG menu/close icons, remove stray class whitespace.
5. **footer.html** — real clickable contact (tel:, mailto:, telegram), fix malformed email, replace dead `#` links.
6. **Page templates** — index, news, detail, elonlar, hodimlar, kutubxona, tadbirlar, aboutUs: semantic classes, remove inline styles, `loading="lazy"` + `decoding="async"` + aspect-ratio images, SVG icons, empty states, accessible iframe `title`.
7. **script.js** — guard null/`#` selectors; scroll → `.scrolled` class via `requestAnimationFrame`; drop redundant JS hover; aria-expanded toggle.
8. **settings.py** — `DEBUG` env (default False); `LANGUAGE_CODE='uz'`, `TIME_ZONE='Asia/Tashkent'`; static/media paths env-overridable with BASE_DIR fallback; fix malformed `STATICFILES_DIRS`; prod security flags gated on `not DEBUG`.

## Performance targets
- Remove infinite hero `float` animation; respect `prefers-reduced-motion`.
- Remove render-blocking Font Awesome CDN (inline SVG instead).
- No layout shift on images (reserve space via aspect-ratio).
- Lazy-load all below-the-fold images.
- No per-scroll-event inline style writes (rAF + class toggle).

## Out of scope
JS framework migration, DB change, Django app restructuring, unrelated refactors.

## Verification
- Code review of every changed file.
- Local dev boot with a dev env (DEBUG on, BASE_DIR static/media). Image-backed pages limited locally (media lives on the server).
- ⚠️ Deploy note: with `DEBUG=False`, confirm nginx/WhiteNoise serves `/media/` and `/static/`.
