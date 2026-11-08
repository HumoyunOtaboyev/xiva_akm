import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Author, Book, Reading, ReadingLog

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

    def test_register_logs_in_and_uses_email_as_username(self):
        res = self.client.post(reverse("kundalik:register"), {
            "first_name": "Aziz",
            "email": "Aziz@Example.com",
            "password1": "Kitob-sevar-2026",
            "password2": "Kitob-sevar-2026",
        })
        self.assertRedirects(res, reverse("kundalik:dashboard"))
        user = User.objects.get()
        self.assertEqual(user.username, "aziz@example.com")
        self.assertEqual(user.email, "aziz@example.com")
        self.assertEqual(user.first_name, "Aziz")
        self.assertEqual(self.client.get(reverse("kundalik:dashboard")).status_code, 200)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user("aziz@example.com", "aziz@example.com", "x")
        res = self.client.post(reverse("kundalik:register"), {
            "first_name": "Aziz",
            "email": "AZIZ@example.com",
            "password1": "Kitob-sevar-2026",
            "password2": "Kitob-sevar-2026",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(User.objects.count(), 1)

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

    def add_book(self, title="O'tkan kunlar", author="Abdulla Qodiriy", pages=360, genre="novel"):
        return self.post("api_add_book", {"title": title, "author": author, "pages": pages, "genre": genre})

    def test_api_requires_login(self):
        self.client.logout()
        res = self.add_book()
        self.assertEqual(res.status_code, 401)
        self.assertEqual(Book.objects.count(), 0)

    def test_api_rejects_get(self):
        res = self.client.get(reverse("kundalik:api_add_book"))
        self.assertEqual(res.status_code, 405)

    def test_add_book_creates_author_book_and_reading(self):
        res = self.add_book()
        self.assertEqual(res.status_code, 200)
        state = res.json()["state"]
        self.assertEqual(len(state["books"]), 1)
        self.assertEqual(state["books"][0]["status"], "want")
        self.assertEqual(Author.objects.get().name, "Abdulla Qodiriy")
        book = Book.objects.get()
        self.assertEqual((book.pages, book.genre, book.created_by), (360, "novel", self.user))

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

    def test_log_updates_progress_and_status(self):
        self.add_book(pages=100)
        reading = Reading.objects.get()
        today = timezone.localdate()

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
        self.assertEqual((reading.current_page, reading.status), (0, "want"))
