from django.urls import path
from .views import register_view, login_view, logout_view

urlpatterns = [
    path("kayit/", register_view, name="register"),
    path("giris/", login_view, name="login"),
    path("cikis/", logout_view, name="logout"),
]
