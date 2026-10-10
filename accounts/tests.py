from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AccountsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mevcutkullanici",
            email="mevcut@example.com",
            password="guvenliParola123!",
        )

    def test_register_page_loads(self):
        """Kayıt sayfası sorunsuz yüklenmeli."""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_register_success_and_auto_login(self):
        """Başarılı kayıt sonrası kullanıcı veritabanına eklenmeli ve otomatik giriş yapılmalı."""
        data = {
            "username": "yeni_uye",
            "email": "yeni@example.com",
            "password": "GuvenliParola456!",
            "password_confirm": "GuvenliParola456!",
        }
        response = self.client.post(reverse("register"), data=data)
        self.assertRedirects(response, reverse("home"))

        # Kullanıcı veritabanında var mı?
        user_exists = User.objects.filter(username="yeni_uye").exists()
        self.assertTrue(user_exists)

        # Oturum açık mı?
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="yeni_uye").id)

    def test_register_duplicate_username(self):
        """Büyük/küçük harf farkı olsa dahi aynı kullanıcı adı reddedilmeli."""
        data = {
            "username": "MEVCUTKULLANICI",
            "email": "farkli@example.com",
            "password": "GuvenliParola456!",
            "password_confirm": "GuvenliParola456!",
        }
        response = self.client.post(reverse("register"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "username",
            "Bu kullanıcı adı zaten alınmış. Farklı bir kullanıcı adı seç.",
        )

    def test_register_duplicate_email(self):
        """Büyük/küçük harf farkı olsa dahi aynı e-posta reddedilmeli."""
        data = {
            "username": "baska_kullanici",
            "email": "MEVCUT@example.com",
            "password": "GuvenliParola456!",
            "password_confirm": "GuvenliParola456!",
        }
        response = self.client.post(reverse("register"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "email",
            "Bu e-posta adresiyle kayıtlı bir hesap zaten var.",
        )

    def test_register_invalid_username_characters(self):
        """Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir (3-20 karakter)."""
        # Çok kısa
        response = self.client.post(
            reverse("register"),
            data={
                "username": "ab",
                "email": "test@example.com",
                "password": "GuvenliParola456!",
                "password_confirm": "GuvenliParola456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

        # Geçersiz karakter
        response = self.client.post(
            reverse("register"),
            data={
                "username": "uye@test",
                "email": "test2@example.com",
                "password": "GuvenliParola456!",
                "password_confirm": "GuvenliParola456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_register_password_mismatch(self):
        """Parola ve parola tekrarı eşleşmiyorsa hata vermeli."""
        data = {
            "username": "farkliparolali",
            "email": "farkli@example.com",
            "password": "GuvenliParola456!",
            "password_confirm": "FarkliParola456!",
        }
        response = self.client.post(reverse("register"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "password_confirm",
            "Girdiğin parolalar birbiriyle eşleşmiyor.",
        )

    def test_login_success(self):
        """Kullanıcı adı ve parola doğruysa giriş yapılmalı ve anasayfaya yönlendirilmeli."""
        data = {
            "username": "mevcutkullanici",
            "password": "guvenliParola123!",
        }
        response = self.client.post(reverse("login"), data=data)
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)

    def test_login_with_next_param(self):
        """Giriş sonrası güvenli 'next' adresine yönlendirilmeli."""
        response = self.client.post(
            f"{reverse('login')}?next=/anket/yeni/",
            data={
                "username": "mevcutkullanici",
                "password": "guvenliParola123!",
            },
        )
        self.assertRedirects(response, "/anket/yeni/")

    def test_login_invalid_credentials(self):
        """Hatalı parolada kullanıcıya anlaşılır hata gösterilmeli."""
        data = {
            "username": "mevcutkullanici",
            "password": "yanlisParola!",
        }
        response = self.client.post(reverse("login"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_logout(self):
        """POST ile çıkış yapıldığında oturum sonlanmalı."""
        self.client.login(username="mevcutkullanici", password="guvenliParola123!")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_email_never_exposed_in_navbar_or_page(self):
        """Giriş yapmış kullanıcının e-postası arayüzde veya kaynak kodda yer almamalı."""
        self.client.login(username="mevcutkullanici", password="guvenliParola123!")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@mevcutkullanici")
        self.assertNotContains(response, "mevcut@example.com")
