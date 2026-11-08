import json
import re
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Author, Book, EmailVerification, PasswordResetCode, Reading, ReadingLog

User = get_user_model()

# Testlarda manifest (collectstatic) talab qilinmasin.
SIMPLE_STATIC = override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)


@SIMPLE_STATIC
class AuthTests(TestCase):
    def test_dashboard_requires_login(self):
        res = self.client.get(reverse("kundalik:dashboard"))
        self.assertRedirects(res, reverse("kundalik:login") + "?next=/kundalik/")

    def test_rest_of_site_is_public(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    PASSWORD = "Kitob-sevar-2026"

    def register(self, email="Aziz@Example.com", name="Aziz", password=PASSWORD):
        return self.client.post(reverse("kundalik:register"), {
            "first_name": name, "email": email, "password1": password, "password2": password,
        })

    def last_code(self):
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    def verify(self, code):
        return self.client.post(reverse("kundalik:verify"), {"code": code})

    def test_register_creates_inactive_user_and_emails_code(self):
        res = self.register()
        self.assertRedirects(res, reverse("kundalik:verify"))
        user = User.objects.get()
        self.assertEqual((user.username, user.email, user.first_name), ("aziz@example.com", "aziz@example.com", "Aziz"))
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["aziz@example.com"])
        code = self.last_code()
        self.assertIn(code, mail.outbox[0].subject)
        self.assertNotEqual(EmailVerification.objects.get().code_hash, code)  # kod ochiq saqlanmaydi
        # Tasdiqlanmaguncha dashboard yopiq.
        self.assertRedirects(self.client.get(reverse("kundalik:dashboard")), reverse("kundalik:login") + "?next=/kundalik/")
        page = self.client.get(reverse("kundalik:verify"))
        self.assertContains(page, "a•••@example.com")

    def test_correct_code_activates_and_logs_in(self):
        self.register()
        res = self.verify(self.last_code())
        self.assertRedirects(res, reverse("kundalik:dashboard"))
        self.assertTrue(User.objects.get().is_active)
        self.assertFalse(EmailVerification.objects.exists())
        self.assertEqual(self.client.get(reverse("kundalik:dashboard")).status_code, 200)
        # Endi oddiy login ishlaydi.
        self.client.logout()
        res = self.client.post(reverse("kundalik:login"), {"username": "aziz@example.com", "password": self.PASSWORD})
        self.assertRedirects(res, reverse("kundalik:dashboard"))

    def test_wrong_code_and_attempt_limit(self):
        self.register()
        code = self.last_code()
        wrong = "000000" if code != "000000" else "111111"
        res = self.verify(wrong)
        self.assertContains(res, "Yana 4 ta urinish qoldi")
        self.assertContains(self.verify("12ab"), "6 xonali kodni kiriting")
        for _ in range(4):
            self.verify(wrong)
        res = self.verify(code)  # to'g'ri kod ham endi qabul qilinmaydi
        self.assertContains(res, "Urinishlar soni tugadi")
        self.assertFalse(User.objects.get().is_active)

    def test_expired_code_rejected(self):
        self.register()
        EmailVerification.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertContains(self.verify(self.last_code()), "muddati tugagan")
        self.assertFalse(User.objects.get().is_active)

    def test_resend_has_cooldown_and_invalidates_old_code(self):
        self.register()
        old = self.last_code()
        res = self.client.post(reverse("kundalik:verify"), {"resend": "1"}, follow=True)
        self.assertContains(res, "soniyadan keyin")
        self.assertEqual(len(mail.outbox), 1)

        EmailVerification.objects.update(last_sent_at=timezone.now() - timedelta(minutes=2))
        res = self.client.post(reverse("kundalik:verify"), {"resend": "1"}, follow=True)
        self.assertContains(res, "Yangi kod yuborildi")
        self.assertEqual(len(mail.outbox), 2)
        new = self.last_code()
        if new != old:
            self.assertContains(self.verify(old), "Kod noto")
        self.assertRedirects(self.verify(new), reverse("kundalik:dashboard"))

    def test_login_with_unverified_account_resends_code(self):
        self.register()
        self.client.logout()
        self.client.session.flush()
        # Noto'g'ri parol — oddiy xato, hech narsa oshkor qilinmaydi.
        res = self.client.post(reverse("kundalik:login"), {"username": "aziz@example.com", "password": "xato"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        # To'g'ri parol (kutish vaqti o'tgan) — yangi kod va tasdiqlash sahifasi.
        EmailVerification.objects.update(last_sent_at=timezone.now() - timedelta(minutes=2))
        res = self.client.post(reverse("kundalik:login"), {"username": "Aziz@example.com", "password": self.PASSWORD})
        self.assertRedirects(res, reverse("kundalik:verify"))
        self.assertEqual(len(mail.outbox), 2)
        self.assertRedirects(self.verify(self.last_code()), reverse("kundalik:dashboard"))

    def test_admin_deactivated_user_cannot_log_in(self):
        User.objects.create_user("blok@example.com", "blok@example.com", self.PASSWORD, is_active=False)
        res = self.client.post(reverse("kundalik:login"), {"username": "blok@example.com", "password": self.PASSWORD})
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 0)

    def test_unverified_email_can_register_again(self):
        self.register(password="Birinchi-parol-1")
        self.client.session.flush()
        res = self.register(name="Aziz K.", password="Ikkinchi-parol-2")
        self.assertRedirects(res, reverse("kundalik:verify"))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertTrue(user.check_password("Ikkinchi-parol-2"))
        self.assertEqual(user.first_name, "Aziz K.")

    def test_register_password_errors_in_uzbek(self):
        res = self.register(password="12345678")
        self.assertContains(res, "faqat raqamlardan")
        self.assertContains(res, "Kamida 8 ta belgi")
        res = self.client.post(reverse("kundalik:register"), {
            "first_name": "Aziz", "email": "a@example.com", "password1": self.PASSWORD, "password2": "boshqa",
        })
        self.assertContains(res, "Parollar bir xil emas")
        self.assertEqual(User.objects.count(), 0)

    def test_register_rejects_verified_email(self):
        User.objects.create_user("aziz@example.com", "aziz@example.com", "x")
        res = self.register(email="AZIZ@example.com")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "allaqachon ro")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_verify_page_without_pending_registration_redirects(self):
        self.assertRedirects(self.client.get(reverse("kundalik:verify")), reverse("kundalik:register"))

    def test_email_send_failure_is_reported(self):
        with mock.patch("kundalik.emails.send_mail", side_effect=OSError("SMTP down")):
            with self.assertLogs("kundalik.emails", level="ERROR"):
                res = self.client.post(reverse("kundalik:register"), {
                    "first_name": "Aziz", "email": "aziz@example.com",
                    "password1": self.PASSWORD, "password2": self.PASSWORD,
                }, follow=True)
        self.assertEqual(res.redirect_chain[-1][0], reverse("kundalik:verify"))
        self.assertContains(res, "Kodni emailga yuborib bo")
        self.assertTrue(EmailVerification.objects.exists())

    def test_admin_can_activate_pending_user(self):
        self.register()
        admin_user = User.objects.create_superuser("admin", "admin@example.com", "x")
        self.client.force_login(admin_user)
        verification = EmailVerification.objects.get()
        self.client.post(reverse("admin:kundalik_emailverification_changelist"), {
            "action": "activate_users", "_selected_action": [verification.pk],
        })
        self.assertTrue(User.objects.get(username="aziz@example.com").is_active)
        self.assertFalse(EmailVerification.objects.exists())

    def test_login_with_email_case_insensitive(self):
        User.objects.create_user("aziz@example.com", "aziz@example.com", "Kitob-sevar-2026")
        res = self.client.post(reverse("kundalik:login"), {
            "username": "Aziz@Example.com", "password": "Kitob-sevar-2026",
        })
        self.assertRedirects(res, reverse("kundalik:dashboard"))

    def test_logout_requires_post(self):
        user = User.objects.create_user("a@a.uz", "a@a.uz", "x")
        self.client.force_login(user)
        res = self.client.post(reverse("kundalik:logout"))
        self.assertRedirects(res, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)


@SIMPLE_STATIC
class PasswordResetTests(TestCase):
    OLD = "Eski-parol-2026"
    NEW = "Yangi-parol-2026"

    def setUp(self):
        self.user = User.objects.create_user("aziz@example.com", "aziz@example.com", self.OLD, first_name="Aziz")

    def request_code(self, email="Aziz@Example.com"):
        return self.client.post(reverse("kundalik:password_reset"), {"email": email})

    def last_code(self):
        return re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

    def confirm(self, code, p1=NEW, p2=None):
        return self.client.post(reverse("kundalik:password_reset_confirm"), {
            "code": code, "new_password1": p1, "new_password2": p2 or p1,
        })

    def test_login_page_links_to_reset(self):
        self.assertContains(self.client.get(reverse("kundalik:login")), reverse("kundalik:password_reset"))

    def test_full_reset_flow(self):
        res = self.request_code()
        self.assertRedirects(res, reverse("kundalik:password_reset_confirm"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("parolni tiklash", mail.outbox[0].subject)
        res = self.confirm(self.last_code())
        self.assertRedirects(res, reverse("kundalik:dashboard"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.NEW))
        self.assertFalse(PasswordResetCode.objects.exists())
        self.client.logout()
        res = self.client.post(reverse("kundalik:login"), {"username": "aziz@example.com", "password": self.NEW})
        self.assertRedirects(res, reverse("kundalik:dashboard"))

    def test_unknown_email_gets_same_response_without_email(self):
        res = self.request_code("yoq@example.com")
        self.assertRedirects(res, reverse("kundalik:password_reset_confirm"))
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(self.confirm("123456"), "Kod noto")

    def test_wrong_code_and_limit(self):
        self.request_code()
        code = self.last_code()
        wrong = "000000" if code != "000000" else "111111"
        self.assertContains(self.confirm(wrong), "Yana 4 ta urinish qoldi")
        for _ in range(4):
            self.confirm(wrong)
        self.assertContains(self.confirm(code), "Urinishlar soni tugadi")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.OLD))

    def test_expired_code(self):
        self.request_code()
        PasswordResetCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertContains(self.confirm(self.last_code()), "muddati tugagan")

    def test_password_validation_does_not_burn_attempts(self):
        self.request_code()
        code = self.last_code()
        self.assertContains(self.confirm(code, p1=self.NEW, p2="Boshqa-parol-2026"), "Parollar bir xil emas")
        res = self.confirm(code, p1="123")
        self.assertContains(res, "Parol juda qisqa")
        self.assertContains(res, "faqat raqamlardan")
        self.assertEqual(PasswordResetCode.objects.get().attempts, 0)
        self.assertRedirects(self.confirm(code), reverse("kundalik:dashboard"))

    def test_resend_cooldown(self):
        self.request_code()
        self.request_code()  # darhol qayta so'rash — yangi xat yuborilmaydi
        self.assertEqual(len(mail.outbox), 1)
        res = self.client.post(reverse("kundalik:password_reset_confirm"), {"resend": "1"}, follow=True)
        self.assertContains(res, "soniyadan keyin")
        PasswordResetCode.objects.update(last_sent_at=timezone.now() - timedelta(minutes=2))
        res = self.client.post(reverse("kundalik:password_reset_confirm"), {"resend": "1"}, follow=True)
        self.assertContains(res, "Yangi kod yuborildi")
        self.assertEqual(len(mail.outbox), 2)

    def test_reset_also_verifies_unverified_account(self):
        self.user.is_active = False
        self.user.save()
        EmailVerification.issue(self.user)
        self.request_code()
        self.assertRedirects(self.confirm(self.last_code()), reverse("kundalik:dashboard"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(EmailVerification.objects.exists())

    def test_blocked_account_gets_no_code(self):
        self.user.is_active = False
        self.user.save()
        self.request_code()
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(self.confirm("123456"), "Kod noto")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_confirm_page_without_request_redirects(self):
        self.assertRedirects(self.client.get(reverse("kundalik:password_reset_confirm")), reverse("kundalik:password_reset"))


@SIMPLE_STATIC
class ApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("aziz@example.com", "aziz@example.com", "x", first_name="Aziz")
        self.other = User.objects.create_user("malika@example.com", "malika@example.com", "x")
        self.client.force_login(self.user)

    def post(self, name, payload=None, **kwargs):
        return self.client.post(
            reverse(f"kundalik:{name}", kwargs=kwargs or None),
            data=json.dumps(payload or {}),
            content_type="application/json",
        )

    def add_book(self, title="O'tkan kunlar", author="Abdulla Qodiriy", pages=360, genre="novel", **extra):
        return self.post("api_add_book", {"title": title, "author": author, "pages": pages, "genre": genre, **extra})

    def search(self, name, q):
        return self.client.get(reverse(f"kundalik:{name}"), {"q": q}).json()["results"]

    def test_api_requires_login(self):
        self.client.logout()
        res = self.add_book()
        self.assertEqual(res.status_code, 401)
        self.assertEqual(Book.objects.count(), 0)

    def test_api_rejects_get(self):
        res = self.client.get(reverse("kundalik:api_add_book"))
        self.assertEqual(res.status_code, 405)

    def test_new_book_is_pending_and_started(self):
        res = self.add_book()
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["notice"], "pending")
        book_state = data["state"]["books"][0]
        self.assertEqual((book_state["status"], book_state["active"]), ("reading", False))
        self.assertEqual(book_state["startedAt"], timezone.localdate().isoformat())
        author = Author.objects.get()
        self.assertEqual((author.name, author.is_active, author.created_by), ("Abdulla Qodiriy", False, self.user))
        book = Book.objects.get()
        self.assertEqual((book.pages, book.genre, book.is_active, book.created_by), (360, "novel", False, self.user))

    def test_want_status_and_start_reading(self):
        state = self.add_book(status="want").json()["state"]
        reading_id = state["books"][0]["id"]
        self.assertEqual(state["books"][0]["status"], "want")
        state = self.post("api_start_reading", pk=reading_id).json()["state"]
        self.assertEqual(state["books"][0]["status"], "reading")

    def test_pending_book_visible_only_to_creator_until_approved(self):
        self.add_book()
        self.assertEqual([r["title"] for r in self.search("api_search_books", "kunlar")], ["O'tkan kunlar"])
        self.assertEqual(len(self.search("api_search_authors", "qodiriy")), 1)

        self.client.force_login(self.other)
        self.assertEqual(self.search("api_search_books", "kunlar"), [])
        self.assertEqual(self.search("api_search_authors", "qodiriy"), [])
        book = Book.objects.get()
        # Boshqa kitobxon tasdiqlanmagan kitobni id bo'yicha ham tanlay olmaydi.
        self.assertEqual(self.post("api_add_book", {"bookId": book.id}).status_code, 404)

        book.is_active = True
        book.save()
        self.assertTrue(Author.objects.get().is_active)  # muallif ham tasdiqlanadi
        results = self.search("api_search_books", "kunlar")
        self.assertEqual((results[0]["id"], results[0]["active"], results[0]["inList"]), (book.id, True, False))
        data = self.post("api_add_book", {"bookId": book.id}).json()
        self.assertEqual(data["notice"], "added")
        self.assertEqual(self.search("api_search_books", "kunlar")[0]["inList"], True)

    def test_search_ignores_case_apostrophe_variants_and_author(self):
        author = Author.objects.create(name="Abdulla Qodiriy", is_active=True)
        Book.objects.create(title="O‘tkan kunlar", author=author, pages=360, is_active=True)
        Book.objects.create(title="Mehrobdan chayon", author=author, pages=300, is_active=True)
        self.assertEqual(len(self.search("api_search_books", "o'TKAN")), 1)
        self.assertEqual(len(self.search("api_search_books", "oʻtkan  kunlar")), 1)
        self.assertEqual(len(self.search("api_search_books", "qodiriy")), 2)
        self.assertEqual(self.search("api_search_books", ""), [])
        # Yozib kiritilgan nom apostrof turi boshqacha bo'lsa ham mavjud kitobga bog'lanadi.
        data = self.add_book(title="o'tkan kunlar", author="abdulla qodiriy").json()
        self.assertEqual(data["notice"], "added")
        self.assertEqual(Book.objects.count(), 2)

    def test_exact_catalog_title_without_author_reuses_book(self):
        author = Author.objects.create(name="Abdulla Qodiriy", is_active=True)
        book = Book.objects.create(title="O‘tkan kunlar", author=author, pages=360, is_active=True)
        res = self.post("api_add_book", {"title": "o'tkan kunlar"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["notice"], "added")
        self.assertEqual(Reading.objects.get().book, book)
        self.assertEqual(Book.objects.count(), 1)
        # Mos kelmasa — muallif so'raladi.
        self.assertEqual(self.post("api_add_book", {"title": "Boshqa kitob"}).json()["error"], "author_required")

    def test_cyrillic_search_is_case_insensitive(self):
        author = Author.objects.create(name="Лев Толстой", is_active=True)
        Book.objects.create(title="Война и мир", author=author, pages=1200, is_active=True)
        self.assertEqual(len(self.search("api_search_books", "ВОЙНА")), 1)
        self.assertEqual(len(self.search("api_search_authors", "толстой")), 1)

    def test_new_book_with_selected_author(self):
        author = Author.objects.create(name="Cho'lpon", is_active=True)
        res = self.post("api_add_book", {"title": "Kecha va kunduz", "authorId": author.id, "pages": 350})
        self.assertEqual(res.status_code, 200)
        book = Book.objects.get()
        self.assertEqual((book.author, book.is_active), (author, False))
        self.assertEqual(Author.objects.count(), 1)

    def test_search_requires_login(self):
        self.client.logout()
        res = self.client.get(reverse("kundalik:api_search_books"), {"q": "a"})
        self.assertEqual(res.status_code, 401)

    def test_same_author_and_book_are_shared_between_users(self):
        self.add_book()
        self.client.force_login(self.other)
        self.assertEqual(self.add_book(title="o'tkan KUNLAR", author="abdulla  qodiriy").status_code, 200)
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Reading.objects.count(), 2)

    def test_duplicate_book_for_same_user_rejected(self):
        self.add_book()
        res = self.add_book()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"], "book_exists")

    def test_add_book_validation(self):
        self.assertEqual(self.add_book(title="  ").json()["error"], "title_required")
        self.assertEqual(self.add_book(author="").json()["error"], "author_required")
        for pages in (0, -5, "abc", "", 10001):
            self.assertEqual(self.add_book(pages=pages).json()["error"], "pages_invalid", pages)
        self.add_book(genre="nonsense")
        self.assertEqual(Book.objects.get().genre, "other")
        self.assertEqual(self.post("api_add_book", {"bookId": 9999}).status_code, 404)

    def test_log_updates_progress_and_status(self):
        self.add_book(pages=100)
        reading = Reading.objects.get()
        today = timezone.localdate()

        self.assertEqual(Reading.objects.get().started_at, today)
        state = self.post("api_add_log", {"bookId": reading.id, "pages": 40, "note": "boshlandi"}).json()["state"]
        self.assertEqual(state["books"][0]["current"], 40)
        self.assertEqual(state["books"][0]["status"], "reading")
        self.assertEqual(state["logs"][0]["date"], today.isoformat())

        state = self.post("api_add_log", {"bookId": reading.id, "pages": 60}).json()["state"]
        book = state["books"][0]
        self.assertEqual((book["current"], book["status"], book["finishedAt"]), (100, "completed", today.isoformat()))
        # Har bir yozuv o'sha paytdagi progressni ko'rsatadi (40%, keyin 100%).
        self.assertEqual([log["progress"] for log in state["logs"]], [100, 40])

    def test_log_validation(self):
        self.add_book(pages=100)
        reading = Reading.objects.get()
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        cases = [
            ({"bookId": reading.id, "pages": 0}, "pages_invalid"),
            ({"bookId": reading.id, "pages": -3}, "pages_invalid"),
            ({"bookId": reading.id, "pages": 101}, "pages_exceed"),
            ({"bookId": reading.id, "pages": 5, "date": tomorrow}, "date_future"),
            ({"bookId": reading.id, "pages": 5, "date": "2026-13-40"}, "date_invalid"),
            ({"bookId": 9999, "pages": 5}, "book_required"),
        ]
        for payload, code in cases:
            res = self.post("api_add_log", payload)
            self.assertEqual(res.status_code, 400, payload)
            self.assertEqual(res.json()["error"], code, payload)
        self.assertEqual(self.post("api_add_log", {"bookId": reading.id, "pages": 101}).json()["params"], {"max": 100})

        self.post("api_add_log", {"bookId": reading.id, "pages": 100})
        res = self.post("api_add_log", {"bookId": reading.id, "pages": 1})
        self.assertEqual(res.json()["error"], "already_completed")

    def test_delete_log_recalculates(self):
        self.add_book(pages=50)
        reading = Reading.objects.get()
        self.post("api_add_log", {"bookId": reading.id, "pages": 20})
        self.post("api_add_log", {"bookId": reading.id, "pages": 30})
        last = ReadingLog.objects.order_by("-id").first()
        state = self.post("api_delete_log", pk=last.id).json()["state"]
        self.assertEqual((state["books"][0]["current"], state["books"][0]["status"]), (20, "reading"))
        self.assertIsNone(state["books"][0]["finishedAt"])

    def test_status_want_until_first_log(self):
        self.add_book(pages=50, status="want")
        reading = Reading.objects.get()
        self.assertEqual(reading.status, "want")
        yesterday = timezone.localdate() - timedelta(days=1)
        self.post("api_add_log", {"bookId": reading.id, "pages": 10, "date": yesterday.isoformat()})
        reading.refresh_from_db()
        self.assertEqual((reading.status, reading.started_at), ("reading", yesterday))
        ReadingLog.objects.get().delete()
        reading.refresh_from_db()
        self.assertEqual(reading.status, "reading")  # boshlagan — holat saqlanadi

    def test_delete_book_removes_reading_but_keeps_catalog(self):
        self.add_book()
        reading = Reading.objects.get()
        self.post("api_add_log", {"bookId": reading.id, "pages": 10})
        state = self.post("api_delete_book", pk=reading.id).json()["state"]
        self.assertEqual(state["books"], [])
        self.assertEqual(ReadingLog.objects.count(), 0)
        self.assertEqual(Book.objects.count(), 1)

    def test_users_cannot_touch_each_others_data(self):
        self.add_book()
        reading = Reading.objects.get()
        self.post("api_add_log", {"bookId": reading.id, "pages": 10})
        log = ReadingLog.objects.get()

        self.client.force_login(self.other)
        self.assertEqual(self.post("api_add_log", {"bookId": reading.id, "pages": 5}).json()["error"], "book_required")
        self.assertEqual(self.post("api_delete_log", pk=log.id).status_code, 404)
        self.assertEqual(self.post("api_delete_book", pk=reading.id).status_code, 404)
        self.assertEqual(ReadingLog.objects.count(), 1)
        res = self.client.get(reverse("kundalik:dashboard"))
        self.assertEqual(res.context["state"]["books"], [])

    def test_dashboard_embeds_state_safely(self):
        self.add_book(title="</script><script>alert(1)</script>")
        res = self.client.get(reverse("kundalik:dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, "</script><script>alert(1)")
        self.assertContains(res, 'id="kundalik-state"')


class ModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("a@a.uz", "a@a.uz", "x")
        author = Author.objects.create(name="Cho'lpon")
        self.book = Book.objects.create(title="Kecha va kunduz", author=author, pages=100)
        self.reading = Reading.objects.create(user=user, book=self.book)

    def test_clean_blocks_overflow_and_future_dates(self):
        ReadingLog.objects.create(reading=self.reading, pages=90)
        with self.assertRaises(ValidationError) as ctx:
            ReadingLog(reading=self.reading, pages=20).full_clean()
        self.assertEqual(ctx.exception.error_dict["pages"][0].code, "pages_exceed")
        with self.assertRaises(ValidationError) as ctx:
            ReadingLog(reading=self.reading, pages=1, date=timezone.localdate() + timedelta(days=1)).full_clean()
        self.assertIn("date", ctx.exception.error_dict)

    def test_changing_book_pages_recalculates_readings(self):
        ReadingLog.objects.create(reading=self.reading, pages=80)
        self.book.pages = 80
        self.book.save()
        self.reading.refresh_from_db()
        self.assertEqual(self.reading.status, Reading.Status.COMPLETED)

    def test_finished_at_is_date_of_completing_log(self):
        today = timezone.localdate()
        ReadingLog.objects.create(reading=self.reading, pages=60, date=today - timedelta(days=3))
        ReadingLog.objects.create(reading=self.reading, pages=40, date=today - timedelta(days=1))
        self.reading.refresh_from_db()
        self.assertEqual(self.reading.finished_at, today - timedelta(days=1))


@SIMPLE_STATIC
class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "x")
        self.client.force_login(self.admin)
        author = Author.objects.create(name="Cho'lpon")
        book = Book.objects.create(title="Kecha va kunduz", author=author, pages=100)
        reading = Reading.objects.create(user=self.admin, book=book)
        ReadingLog.objects.create(reading=reading, pages=10)

    def test_admin_pages_load(self):
        for model in ("author", "book", "reading", "readinglog"):
            url = reverse(f"admin:kundalik_{model}_changelist")
            self.assertEqual(self.client.get(url).status_code, 200, url)
        reading = Reading.objects.get()
        self.assertEqual(self.client.get(reverse("admin:kundalik_reading_change", args=[reading.id])).status_code, 200)

    def test_admin_bulk_delete_logs_recalculates(self):
        reading = Reading.objects.get()
        self.client.post(reverse("admin:kundalik_readinglog_changelist"), {
            "action": "delete_selected",
            "_selected_action": list(ReadingLog.objects.values_list("pk", flat=True)),
            "post": "yes",
        })
        reading.refresh_from_db()
        self.assertEqual((reading.current_page, reading.status), (0, "reading"))

    def test_admin_approve_action_activates_book_and_author(self):
        user = User.objects.create_user("u@u.uz", "u@u.uz", "x")
        author = Author.objects.create(name="Yangi muallif", created_by=user)
        book = Book.objects.create(title="Yangi kitob", author=author, pages=10, created_by=user)
        res = self.client.post(reverse("admin:kundalik_book_changelist"), {
            "action": "approve", "_selected_action": [book.pk],
        })
        self.assertEqual(res.status_code, 302)
        book.refresh_from_db()
        author.refresh_from_db()
        self.assertTrue(book.is_active)
        self.assertTrue(author.is_active)

    def test_admin_add_form_defaults_to_active(self):
        res = self.client.get(reverse("admin:kundalik_book_add"))
        self.assertTrue(res.context["adminform"].form.initial["is_active"])
