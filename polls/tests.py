from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Poll, Option, Vote


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

    # ------------------ Aşama 2: Listeleme ve Oluşturma Testleri ------------------

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

        new_poll = Poll.objects.filter(question="Bu akşam ne yiyelim?").first()
        self.assertIsNotNone(new_poll)
        self.assertEqual(new_poll.author, self.user1)
        self.assertEqual(new_poll.options.count(), 3)
        self.assertEqual(list(new_poll.options.values_list("text", flat=True)), ["Pizza", "Kebap", "Ev yemeği"])
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
        """Detay sayfasında soru ve seçenekler görünmeli."""
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
        """15 anket olduğunda sayfalama çalışmalı."""
        for i in range(15):
            p = Poll.objects.create(question=f"Test Soru {i}", author=self.user1)
            Option.objects.create(poll=p, text="A", position=0)
            Option.objects.create(poll=p, text="B", position=1)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["polls"]), 10)
        self.assertTrue(response.context["page_obj"].has_next())

    # ------------------ Aşama 3: Oy Verme ve Sonuç Testleri ------------------

    def test_member_vote_via_form_post(self):
        """Giriş yapmış üye standart POST ile oy verebilmeli ve sonucu görebilmeli."""
        self.client.login(username="yazar2", password="guvenliParola123!")
        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option1.id},
        )
        self.assertRedirects(response, reverse("poll_detail", kwargs={"poll_id": self.poll.id}))

        # Oy veritabanına kaydedildi mi?
        vote = Vote.objects.filter(poll=self.poll, user=self.user2).first()
        self.assertIsNotNone(vote)
        self.assertEqual(vote.option, self.option1)

        # Detay sayfasında 'Senin Oyun' işareti görünmeli
        detail_response = self.client.get(reverse("poll_detail", kwargs={"poll_id": self.poll.id}))
        self.assertContains(detail_response, "Senin Oyun")

    def test_member_vote_via_ajax_json(self):
        """AJAX ile oy verildiğinde JSON yanıtı (yüzdeler ve toplam oy) dönmeli."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option2.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["total_votes"], 1)
        self.assertEqual(json_data["user_voted_option_id"], self.option2.id)

    def test_anonymous_visitor_vote(self):
        """Ziyaretçi session anahtarıyla oy verebilmeli."""
        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option1.id},
        )
        self.assertRedirects(response, reverse("poll_detail", kwargs={"poll_id": self.poll.id}))

        session_key = self.client.session.session_key
        self.assertIsNotNone(session_key)
        vote = Vote.objects.filter(poll=self.poll, session_key=session_key).first()
        self.assertIsNotNone(vote)
        self.assertIsNone(vote.user)
        self.assertEqual(vote.option, self.option1)

    def test_duplicate_vote_prevention_member(self):
        """Üye aynı ankete ikinci kez oy veremez."""
        self.client.login(username="yazar1", password="guvenliParola123!")
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.user1)

        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option2.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("zaten oy verdin", response.json()["error"])
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)

    def test_duplicate_vote_prevention_visitor(self):
        """Ziyaretçi aynı tarayıcı oturumunda ikinci kez oy veremez."""
        # İlk oy
        self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option1.id},
        )
        # İkinci oy
        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": self.option2.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("zaten oy verdin", response.json()["error"])
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 1)

    def test_vote_option_from_another_poll_rejected(self):
        """Başka bir ankete ait seçenekle oy verilmesi engellenmeli."""
        baska_anket = Poll.objects.create(question="Başka anket", author=self.user1)
        baska_secenek = Option.objects.create(poll=baska_anket, text="C", position=0)

        response = self.client.post(
            reverse("vote_poll", kwargs={"poll_id": self.poll.id}),
            data={"option_id": baska_secenek.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Vote.objects.filter(poll=self.poll).count(), 0)

    def test_percentage_calculation_zero_votes(self):
        """Hiç oy verilmemiş ankette yüzdeler 0 olmalı."""
        response = self.client.get(f"{reverse('poll_detail', kwargs={'poll_id': self.poll.id})}?sonuclar=1")
        self.assertEqual(response.status_code, 200)
        results = response.context["results_data"]
        self.assertEqual(results["total_votes"], 0)
        for opt in results["options"]:
            self.assertEqual(opt["percentage"], 0)
            self.assertEqual(opt["votes_count"], 0)

    def test_percentage_calculation_with_votes(self):
        """Oylar dağıldığında yüzdeler doğru yuvarlanmalı (2 oy Option1, 1 oy Option2 -> %67, %33)."""
        u3 = User.objects.create_user(username="u3", email="u3@example.com", password="pwd")
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.user1)
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.user2)
        Vote.objects.create(poll=self.poll, option=self.option2, user=u3)

        response = self.client.get(f"{reverse('poll_detail', kwargs={'poll_id': self.poll.id})}?sonuclar=1")
        results = response.context["results_data"]
        self.assertEqual(results["total_votes"], 3)

        opt1_data = next(o for o in results["options"] if o["id"] == self.option1.id)
        opt2_data = next(o for o in results["options"] if o["id"] == self.option2.id)

        self.assertEqual(opt1_data["votes_count"], 2)
        self.assertEqual(opt1_data["percentage"], 67)

        self.assertEqual(opt2_data["votes_count"], 1)
        self.assertEqual(opt2_data["percentage"], 33)

    def test_home_card_shows_correct_total_votes(self):
        """Anasayfadaki kartta toplam oy sayısı doğru görünmeli."""
        Vote.objects.create(poll=self.poll, option=self.option1, user=self.user1)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1</strong> oy")
