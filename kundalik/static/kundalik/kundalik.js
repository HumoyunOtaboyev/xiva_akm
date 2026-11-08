"use strict";

(function () {
  /* ---------------- CONFIG & STATE ---------------- */
  const body = document.body;
  const CFG = {
    csrf: body.dataset.csrf,
    loginUrl: body.dataset.loginUrl,
    addBook: body.dataset.apiAddBook,
    searchBooks: body.dataset.apiSearchBooks,
    searchAuthors: body.dataset.apiSearchAuthors,
    startBook: body.dataset.apiStartBook,
    deleteBook: body.dataset.apiDeleteBook,
    addLog: body.dataset.apiAddLog,
    deleteLog: body.dataset.apiDeleteLog,
  };
  let state = JSON.parse(document.getElementById("kundalik-state").textContent);
  let activeFilter = "all";
  let currentLang = "uz";
  const LANG_KEY = "kundalik_lang";
  const $ = (id) => document.getElementById(id);

  /* ---------------- I18N ---------------- */
  const I18N = {
    uz: {
      brand: "O'qish kundaligi", back_to_site: "Saytga qaytish", logout: "Chiqish",
      nav_dashboard: "Dashboard", nav_books: "Mening kitoblarim", nav_log: "O'qish jurnali", nav_stats: "Statistika",
      dash_title: "Dashboard", dash_sub: "Xush kelibsiz, {name}!",
      stat_total: "Jami kitoblar", stat_completed: "Tugallangan", stat_reading: "O'qilmoqda", stat_pages: "O'qilgan sahifalar",
      currently_reading: "Hozir o'qilmoqda", recent_activity: "So'nggi faoliyat",
      no_books_reading: "Hozircha o'qilayotgan kitob yo'q.", no_activity: "Hozircha yozuvlar yo'q. «O'qish jurnali» bo'limida birinchi yozuvni qo'shing.",
      books_title: "Mening kitoblarim", books_sub: "Barcha kitoblaringiz bir joyda", add_book_btn: "+ Kitob qo'shish",
      filter_all: "Barchasi", filter_reading: "O'qilmoqda", filter_completed: "Tugallangan", filter_want: "O'qimoqchiman",
      add_book_section: "Kitob qo'shish", field_author: "Muallif", field_pages: "Sahifalar",
      field_genre: "Janr", btn_add: "Qo'shish",
      no_books_category: "Bu toifada kitob yo'q.", no_books: "Hali kitob qo'shmagansiz. Pastdagi forma orqali birinchi kitobingizni qo'shing.",
      pages_of: "{current} / {pages} bet",
      log_title: "O'qish jurnali", log_sub: "Kunlik o'qish yozuvlaringiz",
      th_date: "Sana", th_book: "Kitob", th_pages_read: "O'qilgan sahifa", th_total_pages: "Jami sahifa",
      th_progress: "Progress", th_note: "Izoh", th_actions: "Amallar", no_logs: "Hozircha yozuvlar yo'q.",
      add_entry: "Yozuv qo'shish", field_book: "Kitob", field_date: "Sana", field_note: "Izoh", btn_save: "Saqlash",
      ph_note: "Qisqa izoh", add_book_first: "Avval kitob qo'shing", completed_suffix: " (tugallangan)",
      stats_title: "Statistika", stats_sub: "O'qish odatlaringiz raqamlarda",
      genre_chart: "Janr bo'yicha kitoblar", day_streak: "Kunlik seriya", pages_read_label: "O'qilgan sahifalar",
      month_chart: "{year}-yilda oylar bo'yicha tugallangan kitoblar", genre_empty: "Hozircha ma'lumot yo'q.",
      months: ["Yan", "Fev", "Mar", "Apr", "May", "Iyn", "Iyl", "Avg", "Sen", "Okt", "Noy", "Dek"],
      status_reading: "O'qilmoqda", status_completed: "Tugallangan", status_want: "O'qimoqchiman",
      unit_pages: "bet", delete: "O'chirish",
      confirm_delete_book: "«{title}» kitobini va uning barcha yozuvlarini o'chirasizmi?",
      confirm_delete_log: "Bu yozuvni o'chirasizmi?",
      genre_novel: "Roman", genre_story: "Hikoya / qissa", genre_poetry: "She'riyat", genre_history: "Tarix",
      genre_science: "Ilmiy", genre_technical: "Texnik", genre_self_help: "Shaxsiy rivojlanish",
      genre_non_fiction: "Hujjatli / ommabop", genre_children: "Bolalar adabiyoti", genre_other: "Boshqa",
      field_book_title: "Kitob nomi", ph_book_search: "Kitob nomi yoki muallifini yozing…",
      ph_author_search: "Muallif ismini yozing…", field_status: "Holati",
      selected_label: "Katalogdan tanlangan kitob", clear_selection: "Tanlovni bekor qilish",
      new_book_hint: "«{title}» katalogda topilmadi — yangi kitob sifatida qo'shiladi. Admin tasdiqlagandan keyin boshqa kitobxonlarga ham ko'rinadi. Muallif, sahifalar soni va janrni to'ldiring.",
      opt_new_book: "«{q}» — yangi kitob sifatida qo'shish", opt_new_author: "«{q}» — yangi muallif sifatida qo'shish",
      opt_pending: "tekshiruvda", opt_in_list: "ro'yxatingizda bor", opt_none: "Katalogda topilmadi",
      status_start: "O'qishni boshladim", status_later: "Keyinroq o'qiyman",
      badge_pending: "⏳ Tekshiruvda", pending_title: "Admin tasdiqlagandan keyin boshqa kitobxonlarga ham ko'rinadi",
      btn_start: "▶ O'qishni boshlash",
      notice_added: "Kitob ro'yxatingizga qo'shildi.",
      notice_pending: "Kitob ro'yxatingizga qo'shildi. Yangi kitob admin tasdiqlagandan keyin katalogda hammaga ko'rinadi.",
      err_title_required: "Kitob nomini kiriting.", err_title_too_long: "Kitob nomi juda uzun.",
      err_author_required: "Muallif ismini kiriting.", err_author_too_long: "Muallif ismi juda uzun.",
      err_pages_invalid: "Sahifalar sonini to'g'ri kiriting (1 – {max}).",
      err_book_exists: "Bu kitob ro'yxatingizda allaqachon bor.",
      err_book_required: "Kitobni tanlang.", err_date_invalid: "Sana noto'g'ri.",
      err_date_future: "Kelajakdagi sanani kiritib bo'lmaydi.",
      err_already_completed: "Bu kitob allaqachon tugallangan.",
      err_pages_exceed: "Bu kitobda faqat {max} bet qolgan.",
      err_not_found: "Ma'lumot topilmadi. Sahifani yangilang.",
      err_server: "Xatolik yuz berdi. Sahifani yangilab, qayta urinib ko'ring.",
    },
    en: {
      brand: "Reading Journal", back_to_site: "Back to site", logout: "Log out",
      nav_dashboard: "Dashboard", nav_books: "My Books", nav_log: "Reading Log", nav_stats: "Statistics",
      dash_title: "Dashboard", dash_sub: "Welcome back, {name}!",
      stat_total: "Total Books", stat_completed: "Completed", stat_reading: "Reading", stat_pages: "Pages Read",
      currently_reading: "Currently Reading", recent_activity: "Recent Activity",
      no_books_reading: "No books currently being read.", no_activity: "No entries yet. Add your first one in the Reading Log.",
      books_title: "My Books", books_sub: "All your books in one place", add_book_btn: "+ Add Book",
      filter_all: "All", filter_reading: "Reading", filter_completed: "Completed", filter_want: "Want to read",
      add_book_section: "Add a Book", field_author: "Author", field_pages: "Pages",
      field_genre: "Genre", btn_add: "Add",
      no_books_category: "No books in this category.", no_books: "You haven't added any books yet. Use the form below to add your first one.",
      pages_of: "{current} / {pages} pages",
      log_title: "Reading Log", log_sub: "Your daily reading entries",
      th_date: "Date", th_book: "Book", th_pages_read: "Pages Read", th_total_pages: "Total Pages",
      th_progress: "Progress", th_note: "Note", th_actions: "Actions", no_logs: "No entries yet.",
      add_entry: "Add Entry", field_book: "Book", field_date: "Date", field_note: "Note", btn_save: "Save",
      ph_note: "Short note", add_book_first: "Add a book first", completed_suffix: " (completed)",
      stats_title: "Statistics", stats_sub: "Your reading habits in numbers",
      genre_chart: "Books by Genre", day_streak: "Day streak", pages_read_label: "Pages read",
      month_chart: "Books completed by month in {year}", genre_empty: "No data yet.",
      months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      status_reading: "Reading", status_completed: "Completed", status_want: "Want to read",
      unit_pages: "pages", delete: "Delete",
      confirm_delete_book: "Delete “{title}” and all its entries?",
      confirm_delete_log: "Delete this entry?",
      genre_novel: "Novel", genre_story: "Short story", genre_poetry: "Poetry", genre_history: "History",
      genre_science: "Science", genre_technical: "Technical", genre_self_help: "Self-help",
      genre_non_fiction: "Non-fiction", genre_children: "Children's", genre_other: "Other",
      field_book_title: "Book title", ph_book_search: "Type a book title or author…",
      ph_author_search: "Type the author's name…", field_status: "Status",
      selected_label: "Book selected from catalog", clear_selection: "Clear selection",
      new_book_hint: "“{title}” isn't in the catalog — it will be added as a new book and becomes visible to other readers after an admin approves it. Fill in the author, pages and genre.",
      opt_new_book: "“{q}” — add as a new book", opt_new_author: "“{q}” — add as a new author",
      opt_pending: "pending review", opt_in_list: "already in your list", opt_none: "Not found in the catalog",
      status_start: "I've started reading", status_later: "I'll read it later",
      badge_pending: "⏳ Pending review", pending_title: "Becomes visible to other readers after an admin approves it",
      btn_start: "▶ Start reading",
      notice_added: "The book was added to your list.",
      notice_pending: "The book was added to your list. New books appear in the shared catalog after an admin approves them.",
      err_title_required: "Enter a book title.", err_title_too_long: "The title is too long.",
      err_author_required: "Enter the author's name.", err_author_too_long: "The author's name is too long.",
      err_pages_invalid: "Enter a valid number of pages (1 – {max}).",
      err_book_exists: "This book is already in your list.",
      err_book_required: "Select a book.", err_date_invalid: "Invalid date.",
      err_date_future: "The date can't be in the future.",
      err_already_completed: "This book is already completed.",
      err_pages_exceed: "Only {max} pages are left in this book.",
      err_not_found: "Not found. Please reload the page.",
      err_server: "Something went wrong. Reload the page and try again.",
    },
    ru: {
      brand: "Дневник чтения", back_to_site: "Вернуться на сайт", logout: "Выйти",
      nav_dashboard: "Панель", nav_books: "Мои книги", nav_log: "Журнал чтения", nav_stats: "Статистика",
      dash_title: "Панель", dash_sub: "С возвращением, {name}!",
      stat_total: "Всего книг", stat_completed: "Завершено", stat_reading: "Читаю", stat_pages: "Страниц прочитано",
      currently_reading: "Сейчас читаю", recent_activity: "Последняя активность",
      no_books_reading: "Нет книг в процессе чтения.", no_activity: "Записей пока нет. Добавьте первую в «Журнале чтения».",
      books_title: "Мои книги", books_sub: "Все ваши книги в одном месте", add_book_btn: "+ Добавить книгу",
      filter_all: "Все", filter_reading: "Читаю", filter_completed: "Завершено", filter_want: "Хочу прочитать",
      add_book_section: "Добавить книгу", field_author: "Автор", field_pages: "Страницы",
      field_genre: "Жанр", btn_add: "Добавить",
      no_books_category: "В этой категории нет книг.", no_books: "Вы ещё не добавили ни одной книги. Добавьте первую с помощью формы ниже.",
      pages_of: "{current} / {pages} стр.",
      log_title: "Журнал чтения", log_sub: "Ваши ежедневные записи чтения",
      th_date: "Дата", th_book: "Книга", th_pages_read: "Стр. прочитано", th_total_pages: "Всего страниц",
      th_progress: "Прогресс", th_note: "Заметка", th_actions: "Действия", no_logs: "Записей пока нет.",
      add_entry: "Добавить запись", field_book: "Книга", field_date: "Дата", field_note: "Заметка", btn_save: "Сохранить",
      ph_note: "Короткая заметка", add_book_first: "Сначала добавьте книгу", completed_suffix: " (завершена)",
      stats_title: "Статистика", stats_sub: "Ваши привычки чтения в цифрах",
      genre_chart: "Книги по жанрам", day_streak: "Дней подряд", pages_read_label: "Страниц прочитано",
      month_chart: "Завершённые книги по месяцам, {year}", genre_empty: "Данных пока нет.",
      months: ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
      status_reading: "Читаю", status_completed: "Завершено", status_want: "Хочу прочитать",
      unit_pages: "стр.", delete: "Удалить",
      confirm_delete_book: "Удалить «{title}» и все её записи?",
      confirm_delete_log: "Удалить эту запись?",
      genre_novel: "Роман", genre_story: "Рассказ / повесть", genre_poetry: "Поэзия", genre_history: "История",
      genre_science: "Наука", genre_technical: "Техническая", genre_self_help: "Саморазвитие",
      genre_non_fiction: "Нон-фикшн", genre_children: "Детская", genre_other: "Другое",
      field_book_title: "Название книги", ph_book_search: "Введите название книги или автора…",
      ph_author_search: "Введите имя автора…", field_status: "Статус",
      selected_label: "Книга из каталога", clear_selection: "Отменить выбор",
      new_book_hint: "«{title}» нет в каталоге — она будет добавлена как новая книга и станет видна другим читателям после проверки администратором. Укажите автора, число страниц и жанр.",
      opt_new_book: "«{q}» — добавить как новую книгу", opt_new_author: "«{q}» — добавить как нового автора",
      opt_pending: "на проверке", opt_in_list: "уже в вашем списке", opt_none: "В каталоге не найдено",
      status_start: "Я начал(а) читать", status_later: "Прочитаю позже",
      badge_pending: "⏳ На проверке", pending_title: "Станет видна другим читателям после проверки администратором",
      btn_start: "▶ Начать читать",
      notice_added: "Книга добавлена в ваш список.",
      notice_pending: "Книга добавлена в ваш список. Новые книги появляются в общем каталоге после проверки администратором.",
      err_title_required: "Введите название книги.", err_title_too_long: "Название слишком длинное.",
      err_author_required: "Введите имя автора.", err_author_too_long: "Имя автора слишком длинное.",
      err_pages_invalid: "Введите корректное число страниц (1 – {max}).",
      err_book_exists: "Эта книга уже есть в вашем списке.",
      err_book_required: "Выберите книгу.", err_date_invalid: "Неверная дата.",
      err_date_future: "Дата не может быть в будущем.",
      err_already_completed: "Эта книга уже завершена.",
      err_pages_exceed: "В этой книге осталось только {max} стр.",
      err_not_found: "Не найдено. Обновите страницу.",
      err_server: "Произошла ошибка. Обновите страницу и попробуйте снова.",
    },
  };

  function t(key, params) {
    const dict = I18N[currentLang] || I18N.uz;
    let val = key in dict ? dict[key] : (key in I18N.uz ? I18N.uz[key] : key);
    if (params && typeof val === "string") {
      val = val.replace(/\{(\w+)\}/g, (m, k) => (k in params ? params[k] : m));
    }
    return val;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
  }

  function applyStaticTranslations() {
    document.documentElement.lang = currentLang;
    document.title = t("brand") + " — Xiva shahar AKM";
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    document.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
  }

  function setLanguage(lang) {
    currentLang = I18N[lang] ? lang : "uz";
    try { localStorage.setItem(LANG_KEY, currentLang); } catch (e) { /* ignore */ }
    $("lang-select").value = currentLang;
    applyStaticTranslations();
    clearErrors();
    renderAll();
    updateBookForm();
  }

  /* ---------------- HELPERS ---------------- */
  const findBook = (id) => state.books.find((b) => b.id === id);
  const pct = (b) => (b.pages ? Math.min(100, Math.round((b.current / b.pages) * 100)) : 0);
  const statusLabel = (s) => t("status_" + s);
  const genreLabel = (g) => t("genre_" + g);

  // "YYYY-MM-DD" bilan UTC'da ishlaymiz — vaqt mintaqasi siljishlarisiz.
  const parseDay = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)); };
  const fmtDay = (d) => d.toISOString().slice(0, 10);

  function initials(name) {
    return (name || "?").trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  }

  function clearErrors() {
    $("book-error").textContent = "";
    $("book-notice").textContent = "";
    $("log-error").textContent = "";
  }

  // Apostrof turlari (o' oʻ o‘ o’ o`) va bo'shliqlarga befarq taqqoslash
  const norm = (s) => String(s || "").toLowerCase().replace(/[`'ʻʼ‘’]/g, "'").replace(/\s+/g, " ").trim();

  function highlight(text, q) {
    const src = String(text);
    const i = norm(src).indexOf(norm(q));
    if (!q || i < 0 || norm(src).length !== src.toLowerCase().length) return esc(src);
    return esc(src.slice(0, i)) + "<mark>" + esc(src.slice(i, i + norm(q).length)) + "</mark>" + esc(src.slice(i + norm(q).length));
  }

  /* ---------------- API ---------------- */
  async function api(url, payload) {
    let res;
    try {
      res = await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": CFG.csrf },
        body: JSON.stringify(payload || {}),
      });
    } catch (e) {
      throw { error: "server" };
    }
    let data = null;
    try { data = await res.json(); } catch (e) { /* HTML javob (masalan, CSRF xatosi) */ }
    if (res.status === 401) {
      window.location.href = CFG.loginUrl + "?next=" + encodeURIComponent(window.location.pathname);
      throw { error: "auth" };
    }
    if (!res.ok || !data || !data.state) {
      throw data && data.error ? data : { error: "server" };
    }
    state = data.state;
    renderAll();
    return data;
  }

  function showError(el, err) {
    if (err.error === "auth") return;
    el.textContent = t("err_" + err.error, err.params || {});
    if (el.textContent === "err_" + err.error) el.textContent = t("err_server");
  }

  async function withBusy(button, fn) {
    if (button.disabled) return;
    button.disabled = true;
    try { await fn(); } finally { button.disabled = false; }
  }

  /* ---------------- NAV ---------------- */
  function showTab(tab) {
    document.querySelectorAll(".nav-item[data-tab]").forEach((b) => {
      const on = b.dataset.tab === tab;
      b.classList.toggle("active", on);
      if (on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
    });
    document.querySelectorAll(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + tab));
    if (tab === "stats") renderStats();
  }

  /* ---------------- RENDER ---------------- */
  function renderDashboard() {
    const name = $("user-name").textContent.trim();
    $("dash-sub").textContent = t("dash_sub", { name });
    const books = state.books;
    const completed = books.filter((b) => b.status === "completed").length;
    const reading = books.filter((b) => b.status === "reading");
    const pagesTotal = state.logs.reduce((s, l) => s + l.pages, 0);
    $("dash-stats").innerHTML = [
      [books.length, "stat_total"], [completed, "stat_completed"], [reading.length, "stat_reading"], [pagesTotal, "stat_pages"],
    ].map(([n, k]) => `<div class="stat-card"><div class="stat-num">${n}</div><div class="stat-label">${t(k)}</div></div>`).join("");

    $("dash-reading").innerHTML = reading.length ? reading.map((b) => `
      <div class="reading-row">
        <div class="rr-body">
          <div class="rr-title">${esc(b.title)}</div>
          <div class="rr-author">${esc(b.author)} · ${t("pages_of", { current: b.current, pages: b.pages })}</div>
          <div class="progress-track"><div class="progress-fill reading" style="width:${pct(b)}%"></div></div>
        </div>
        <div class="rr-pct">${pct(b)}%</div>
      </div>`).join("") : `<p class="muted">${t("no_books_reading")}</p>`;

    const recent = state.logs.slice(0, 5);
    $("dash-activity").innerHTML = recent.length ? recent.map((l) => {
      const b = findBook(l.readingId);
      return `<div class="activity-item">
        <div class="activity-dot"></div>
        <div><span class="activity-date">${l.date}</span> — ${b ? esc(b.title) : "—"}: <strong>${l.pages} ${t("unit_pages")}</strong>${l.note ? " — " + esc(l.note) : ""}</div>
      </div>`;
    }).join("") : `<p class="muted">${t("no_activity")}</p>`;
  }

  function renderFilters() {
    const count = (k) => (k === "all" ? state.books.length : state.books.filter((b) => b.status === k).length);
    $("book-filters").innerHTML = ["all", "reading", "completed", "want"].map((k) =>
      `<button type="button" class="filter-btn ${activeFilter === k ? "active" : ""}" data-filter="${k}" aria-pressed="${activeFilter === k}">${t("filter_" + k)} <span class="filter-count">${count(k)}</span></button>`
    ).join("");
  }

  function renderBooks() {
    const list = activeFilter === "all" ? state.books : state.books.filter((b) => b.status === activeFilter);
    const empty = state.books.length ? t("no_books_category") : t("no_books");
    $("book-grid").innerHTML = list.map((b) => `
      <div class="book-card">
        <button type="button" class="icon-btn" data-delete-book="${b.id}" title="${t("delete")}" aria-label="${t("delete")}: ${esc(b.title)}">🗑</button>
        <div class="book-title">${esc(b.title)}</div>
        <div class="book-author">${esc(b.author)}</div>
        <div class="book-meta">${esc(genreLabel(b.genre))} · ${t("pages_of", { current: b.current, pages: b.pages })}</div>
        <div class="badge-row">
          <span class="badge ${b.status}">${statusLabel(b.status)}</span>
          ${b.active ? "" : `<span class="badge pending" title="${esc(t("pending_title"))}">${t("badge_pending")}</span>`}
        </div>
        <div class="progress-row">
          <div class="progress-track"><div class="progress-fill ${b.status}" style="width:${pct(b)}%"></div></div>
          <span class="book-pct">${pct(b)}%</span>
        </div>
        ${b.status === "want" ? `<button type="button" class="btn-small" data-start-book="${b.id}">${t("btn_start")}</button>` : ""}
      </div>`).join("") || `<p class="muted">${empty}</p>`;
  }

  function populateSelect() {
    const sel = $("nl-book");
    const prev = Number(sel.value);
    const available = state.books.filter((b) => b.status !== "completed");
    if (!state.books.length) {
      sel.innerHTML = `<option value="">${t("add_book_first")}</option>`;
      return;
    }
    sel.innerHTML = state.books.map((b) => {
      const done = b.status === "completed";
      return `<option value="${b.id}" ${done ? "disabled" : ""}>${esc(b.title)}${done ? t("completed_suffix") : ""}</option>`;
    }).join("");
    const keep = available.find((b) => b.id === prev) || available[0];
    if (keep) sel.value = keep.id;
  }

  function renderLog() {
    $("log-list").innerHTML = state.logs.map((l) => {
      const b = findBook(l.readingId);
      const cls = l.progress >= 100 ? "completed" : "reading";
      return `<tr>
        <td class="nowrap">${l.date}</td>
        <td>${b ? esc(b.title) : "—"}</td>
        <td class="pages">+${l.pages}</td>
        <td>${b ? b.pages : "—"}</td>
        <td><div class="log-progress"><div class="progress-track"><div class="progress-fill ${cls}" style="width:${l.progress}%"></div></div><span class="log-pct">${l.progress}%</span></div></td>
        <td>${esc(l.note)}</td>
        <td><button type="button" class="icon-btn" data-delete-log="${l.id}" title="${t("delete")}" aria-label="${t("delete")}">🗑</button></td>
      </tr>`;
    }).join("") || `<tr><td colspan="7" class="muted">${t("no_logs")}</td></tr>`;
  }

  function renderStats() {
    // Janrlar
    const genreCounts = {};
    state.books.forEach((b) => { genreCounts[b.genre] = (genreCounts[b.genre] || 0) + 1; });
    const entries = Object.entries(genreCounts).sort((a, b) => b[1] - a[1]);
    const maxG = Math.max(1, ...entries.map((e) => e[1]));
    $("genre-chart").innerHTML = entries.map(([g, c]) => `
      <div class="bar-row">
        <div class="bar-label">${esc(genreLabel(g))}</div>
        <div class="bar-track2"><div class="bar-fill2" style="width:${(c / maxG) * 100}%"></div></div>
        <div class="bar-val">${c}</div>
      </div>`).join("") || `<p class="muted">${t("genre_empty")}</p>`;

    // Oylar bo'yicha — haqiqiy tugatilgan sanalar, joriy yil
    const year = Number(state.today.slice(0, 4));
    const counts = new Array(12).fill(0);
    state.books.forEach((b) => {
      if (b.finishedAt && Number(b.finishedAt.slice(0, 4)) === year) counts[Number(b.finishedAt.slice(5, 7)) - 1]++;
    });
    const maxM = Math.max(1, ...counts);
    $("month-chart-title").textContent = t("month_chart", { year });
    $("month-chart").innerHTML = `<div class="month-chart">` + t("months").map((m, i) => `
      <div class="month-col">
        <div class="month-val">${counts[i] || ""}</div>
        <div class="month-bar ${counts[i] ? "" : "empty"}" style="height:${counts[i] ? Math.max(6, (counts[i] / maxM) * 80) : 3}px"></div>
        <div class="month-name">${m}</div>
      </div>`).join("") + `</div>`;

    $("pages-total").textContent = state.logs.reduce((s, l) => s + l.pages, 0);

    // Kunlik seriya: bugundan (bugun hali yozuv bo'lmasa — kechadan) orqaga
    const days = new Set(state.logs.map((l) => l.date));
    const d = parseDay(state.today);
    if (!days.has(fmtDay(d))) d.setUTCDate(d.getUTCDate() - 1);
    let streak = 0;
    while (days.has(fmtDay(d))) { streak++; d.setUTCDate(d.getUTCDate() - 1); }
    $("streak-num").textContent = streak;
  }

  function renderAll() {
    renderDashboard();
    renderFilters();
    renderBooks();
    populateSelect();
    renderLog();
    if ($("page-stats").classList.contains("active")) renderStats();
    const dateInput = $("nl-date");
    dateInput.max = state.today;
    if (!dateInput.value || dateInput.value > state.today) dateInput.value = state.today;
  }

  /* ---------------- EVENTS ---------------- */
  document.querySelectorAll(".nav-item[data-tab]").forEach((btn) => {
    btn.addEventListener("click", () => showTab(btn.dataset.tab));
  });

  $("lang-select").addEventListener("change", (e) => setLanguage(e.target.value));
  $("focus-add-book").addEventListener("click", () => $("nb-title").focus());

  $("book-filters").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-filter]");
    if (!btn) return;
    activeFilter = btn.dataset.filter;
    renderFilters();
    renderBooks();
  });

  /* ---------------- COMBOBOX (qidiruv bilan tanlash) ---------------- */
  function makeCombo({ input, list, url, buildItems, onType }) {
    let items = [];
    let active = -1;
    let timer = null;
    let seq = 0;

    const close = () => {
      list.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    };
    const render = () => {
      list.innerHTML = items.map((it, i) =>
        `<li role="option" id="${list.id}-${i}" data-i="${i}" class="combo-opt ${it.cls || ""}" aria-disabled="${!it.pick}">${it.html}</li>`
      ).join("");
      list.hidden = !items.length;
      input.setAttribute("aria-expanded", String(!list.hidden));
      active = -1;
    };
    const setActive = (i) => {
      const opts = list.querySelectorAll(".combo-opt");
      opts.forEach((o) => o.classList.remove("active"));
      active = i;
      if (i >= 0 && opts[i]) {
        opts[i].classList.add("active");
        opts[i].scrollIntoView({ block: "nearest" });
        input.setAttribute("aria-activedescendant", opts[i].id);
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    };
    const move = (dir) => {
      if (!items.some((it) => it.pick)) return;
      let i = active;
      do { i = (i + dir + items.length) % items.length; } while (!items[i].pick);
      setActive(i);
    };
    const pick = (i) => {
      const it = items[i];
      if (!it || !it.pick) return;
      close();
      it.pick();
    };
    const search = async () => {
      const q = input.value.trim();
      const mine = ++seq;
      if (!q) { items = []; close(); return; }
      let results = [];
      try {
        const res = await fetch(url + "?q=" + encodeURIComponent(q), { credentials: "same-origin" });
        if (res.status === 401) { window.location.href = CFG.loginUrl; return; }
        if (res.ok) results = (await res.json()).results || [];
      } catch (e) { /* tarmoq xatosi — natijasiz davom etamiz */ }
      if (mine !== seq || document.activeElement !== input) return;
      items = buildItems(results, q);
      render();
    };

    input.addEventListener("input", () => {
      onType();
      clearTimeout(timer);
      timer = setTimeout(search, 200);
    });
    input.addEventListener("focus", () => { if (input.value.trim()) search(); });
    input.addEventListener("blur", () => setTimeout(close, 120));
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); if (list.hidden) search(); else move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); if (!list.hidden) move(-1); }
      else if (e.key === "Enter" && !list.hidden && active >= 0) { e.preventDefault(); pick(active); }
      else if (e.key === "Escape" && !list.hidden) { e.preventDefault(); close(); }
    });
    list.addEventListener("mousedown", (e) => {
      e.preventDefault(); // inputdan fokus ketmasin
      const li = e.target.closest("[data-i]");
      if (li) pick(Number(li.dataset.i));
    });
    return { close };
  }

  /* ---------------- KITOB QO'SHISH ---------------- */
  let selectedBook = null;   // katalogdan tanlangan kitob
  let selectedAuthor = null; // katalogdan tanlangan muallif
  const titleInput = $("nb-title");
  const authorInput = $("nb-author");

  function updateBookForm() {
    const hasBook = !!selectedBook;
    $("selected-book").hidden = !hasBook;
    $("new-book-fields").hidden = hasBook;
    if (hasBook) {
      $("sel-title").textContent = selectedBook.title;
      $("sel-meta").textContent = `${selectedBook.author} · ${selectedBook.pages} ${t("unit_pages")} · ${genreLabel(selectedBook.genre)}` +
        (selectedBook.active ? "" : ` · ${t("opt_pending")}`);
    }
    const title = titleInput.value.trim();
    const hint = $("new-book-hint");
    hint.hidden = hasBook || !title;
    hint.textContent = title ? t("new_book_hint", { title }) : "";
  }

  function selectBook(book) {
    selectedBook = book;
    titleInput.value = book.title;
    clearErrors();
    updateBookForm();
  }

  function selectAuthor(author) {
    selectedAuthor = author;
    authorInput.value = author.name;
    $("nb-pages").focus();
  }

  function resetBookForm() {
    selectedBook = null;
    selectedAuthor = null;
    titleInput.value = "";
    authorInput.value = "";
    $("nb-pages").value = "";
    $("nb-genre").value = "other";
    updateBookForm();
  }

  makeCombo({
    input: titleInput,
    list: $("nb-title-list"),
    url: CFG.searchBooks,
    onType: () => {
      if (selectedBook && titleInput.value !== selectedBook.title) selectedBook = null;
      $("book-notice").textContent = "";
      updateBookForm();
    },
    buildItems: (results, q) => {
      const items = results.map((r) => ({
        cls: r.inList ? "disabled" : "",
        html: `<span class="opt-title">${highlight(r.title, q)}` +
          (r.active ? "" : `<span class="opt-tag">${t("opt_pending")}</span>`) +
          (r.inList ? `<span class="opt-tag in-list">${t("opt_in_list")}</span>` : "") +
          `</span><span class="opt-meta">${highlight(r.author, q)} · ${r.pages} ${t("unit_pages")} · ${esc(genreLabel(r.genre))}</span>`,
        pick: r.inList ? null : () => selectBook(r),
      }));
      if (!results.some((r) => norm(r.title) === norm(q))) {
        if (!results.length) items.push({ cls: "empty", html: t("opt_none"), pick: null });
        items.push({ cls: "create", html: "＋ " + esc(t("opt_new_book", { q })), pick: () => { updateBookForm(); authorInput.focus(); } });
      }
      return items;
    },
  });

  makeCombo({
    input: authorInput,
    list: $("nb-author-list"),
    url: CFG.searchAuthors,
    onType: () => {
      if (selectedAuthor && authorInput.value !== selectedAuthor.name) selectedAuthor = null;
    },
    buildItems: (results, q) => {
      const items = results.map((a) => ({
        html: `<span class="opt-title">${highlight(a.name, q)}` +
          (a.active ? "" : `<span class="opt-tag">${t("opt_pending")}</span>`) + `</span>`,
        pick: () => selectAuthor(a),
      }));
      if (!results.some((a) => norm(a.name) === norm(q))) {
        items.push({ cls: "create", html: "＋ " + esc(t("opt_new_author", { q })), pick: () => $("nb-pages").focus() });
      }
      return items;
    },
  });

  $("sel-clear").addEventListener("click", () => {
    selectedBook = null;
    titleInput.value = "";
    updateBookForm();
    titleInput.focus();
  });

  $("add-book-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const errEl = $("book-error");
    const button = e.target.querySelector("button[type=submit]");
    clearErrors();
    const status = e.target.querySelector("input[name=nb-status]:checked").value;
    const payload = selectedBook
      ? { bookId: selectedBook.id, status }
      : {
          title: titleInput.value.trim(),
          author: authorInput.value.trim(),
          authorId: selectedAuthor ? selectedAuthor.id : "",
          pages: $("nb-pages").value,
          genre: $("nb-genre").value,
          status,
        };
    withBusy(button, async () => {
      try {
        const data = await api(CFG.addBook, payload);
        resetBookForm();
        $("book-notice").textContent = t(data.notice === "pending" ? "notice_pending" : "notice_added");
      } catch (err) { showError(errEl, err); }
    });
  });

  $("add-log-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const errEl = $("log-error");
    const button = e.target.querySelector("button[type=submit]");
    errEl.textContent = "";
    withBusy(button, async () => {
      try {
        await api(CFG.addLog, {
          bookId: $("nl-book").value,
          date: $("nl-date").value,
          pages: $("nl-pages").value,
          note: $("nl-note").value.trim(),
        });
        $("nl-pages").value = "";
        $("nl-note").value = "";
      } catch (err) { showError(errEl, err); }
    });
  });

  $("book-grid").addEventListener("click", (e) => {
    const startBtn = e.target.closest("[data-start-book]");
    if (startBtn) {
      const id = Number(startBtn.dataset.startBook);
      withBusy(startBtn, async () => {
        try { await api(CFG.startBook.replace("/0/", "/" + id + "/")); }
        catch (err) { showError($("book-error"), err); }
      });
      return;
    }
    const btn = e.target.closest("[data-delete-book]");
    if (!btn) return;
    const id = Number(btn.dataset.deleteBook);
    const b = findBook(id);
    if (!window.confirm(t("confirm_delete_book", { title: b ? b.title : "" }))) return;
    withBusy(btn, async () => {
      try { await api(CFG.deleteBook.replace("/0/", "/" + id + "/")); }
      catch (err) { showError($("book-error"), err); }
    });
  });

  $("log-list").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-delete-log]");
    if (!btn) return;
    if (!window.confirm(t("confirm_delete_log"))) return;
    const id = Number(btn.dataset.deleteLog);
    withBusy(btn, async () => {
      try { await api(CFG.deleteLog.replace("/0/", "/" + id + "/")); }
      catch (err) { showError($("log-error"), err); }
    });
  });

  /* ---------------- INIT ---------------- */
  $("user-avatar").textContent = initials($("user-name").textContent);
  let savedLang = null;
  try { savedLang = localStorage.getItem(LANG_KEY); } catch (e) { /* ignore */ }
  setLanguage(savedLang || "uz");
})();
