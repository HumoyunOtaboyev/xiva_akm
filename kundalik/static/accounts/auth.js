"use strict";
// Header'dagi foydalanuvchi menyusi (<details>): tashqariga bosilganda yoki Esc bosilganda yopiladi.
(function () {
  var menus = document.querySelectorAll("details.user-menu");
  if (!menus.length) return;
  document.addEventListener("click", function (e) {
    menus.forEach(function (m) {
      if (m.open && !m.contains(e.target)) m.open = false;
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    menus.forEach(function (m) {
      if (m.open) {
        m.open = false;
        m.querySelector("summary").focus();
      }
    });
  });
})();
