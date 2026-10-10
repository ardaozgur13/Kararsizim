from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Poll, Option


class PollsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="yazar1",
            email="yazar1@example.com",
            password="guvenliParola123!",
        )
        self.user2 = User.objects.create_user(
            username="yazar2",
            email="yazar2@example.com",
            password="guvenliParola123!",
        )

        self.poll = Poll.objects.create(
            question="Hangi filmi izleyelim?",
            author=self.user1,
        )
        self.option1 = Option.objects.create(poll=self.poll, text="Interstellar", position=0)
        self.option2 = Option.objects.create(poll=self.poll, text="Inception", position=1)

    def test_home_page_accessible_by_anonymous_user(self):
        """Ziyaretçi anasayfayı görebilmeli ve anket listelenmeli."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hangi filmi izleyelim?")
        self.assertContains(response, "@yazar1")
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "Inception")

    def test_create_poll_requires_login(self):
        """Giriş yapmamış kullanıcı anket oluşturma sayfasına gittiğinde login'e yönlendirilmeli."""
        response = self.client.get(reverse("create_poll"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_poll')}")

    def test_create_poll_success_logged_in_user(self):
        """Giriş yapmış kullanıcı geçerli verilerle anket açabilmeli."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        data = {
            "question": "Bu akşam ne yiyelim?",
            "options": ["Pizza", "Kebap", "Ev yemeği"],
        }
        response = self.client.post(reverse("create_poll"), data=data)

        # Yeni anket oluştu mu?
        new_poll = Poll.objects.filter(question="Bu akşam ne yiyelim?").first()
        self.assertIsNotNone(new_poll)
        self.assertEqual(new_poll.author, self.user1)
        self.assertEqual(new_poll.options.count(), 3)
        self.assertEqual(list(new_poll.options.values_list("text", flat=True)), ["Pizza", "Kebap", "Ev yemeği"])

        # Detay sayfasına yönlendirme
        self.assertRedirects(response, reverse("poll_detail", kwargs={"poll_id": new_poll.id}))

    def test_create_poll_min_options_validation(self):
        """En az 2 seçenek girilmediğinde anket oluşturulamaz."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        data = {
            "question": "Tek seçenekli soru",
            "options": ["Sadece Bu"],
        }
        response = self.client.post(reverse("create_poll"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            None,
            "Bir anket oluşturmak için en az 2 seçenek girmelisin.",
        )

    def test_create_poll_max_options_validation(self):
        """5'ten fazla seçenek girilirse form hata vermeli."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        data = {
            "question": "Çok seçenekli soru",
            "options": ["1", "2", "3", "4", "5", "6"],
        }
        response = self.client.post(reverse("create_poll"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            None,
            "Bir ankette en fazla 5 seçenek bulunabilir.",
        )

    def test_create_poll_duplicate_options_validation(self):
        """Büyük/küçük harf veya boşluk farkı olan yinelenen seçenekler reddedilmeli."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        data = {
            "question": "Aynı seçenekli soru",
            "options": ["Pizza", "  pizza  ", "Burger"],
        }
        response = self.client.post(reverse("create_poll"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_poll_detail_view(self):
        """Detay sayfasında soru ve tüm seçenekler görünmeli."""
        response = self.client.get(reverse("poll_detail", kwargs={"poll_id": self.poll.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.question)
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "Inception")

    def test_delete_poll_by_author(self):
        """Anket sahibi kendi anketini silebilir."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        response = self.client.post(reverse("delete_poll", kwargs={"poll_id": self.poll.id}))
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(Poll.objects.filter(id=self.poll.id).exists())

    def test_delete_poll_by_unauthorized_user(self):
        """Başka bir kullanıcı anketi silmeye çalışırsa 403 Forbidden almalı."""
        self.client.login(username="yazar2", password="guvenliParola123!")
        response = self.client.post(reverse("delete_poll", kwargs={"poll_id": self.poll.id}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Poll.objects.filter(id=self.poll.id).exists())

    def test_delete_poll_by_anonymous_user(self):
        """Giriş yapmamış kullanıcı anket silmeye kalkarsa login'e yönlendirilmeli."""
        response = self.client.post(reverse("delete_poll", kwargs={"poll_id": self.poll.id}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Poll.objects.filter(id=self.poll.id).exists())

    def test_my_polls_view(self):
        """Kullanıcı kendi anketlerini /profilim/ sayfasında görebilmeli."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        response = self.client.get(reverse("my_polls"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.poll.question)

    def test_pagination(self):
        """15 anket olduğunda sayfalama çalışmalı ve ilk sayfada 10 anket olmalı."""
        for i in range(15):
            p = Poll.objects.create(question=f"Test Soru {i}", author=self.user1)
            Option.objects.create(poll=p, text="A", position=0)
            Option.objects.create(poll=p, text="B", position=1)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["polls"]), 10)
        self.assertTrue(response.context["page_obj"].has_next())

        # İkinci sayfa
        response_page2 = self.client.get(f"{reverse('home')}?page=2")
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context["polls"]), 6)  # 15 + 1 (setUp) = 16 -> 10 + 6
