from django.urls import path
from .views import home_view, create_poll_view, my_polls_view

urlpatterns = [
    path("", home_view, name="home"),
    path("anket/yeni/", create_poll_view, name="create_poll"),
    path("profilim/", my_polls_view, name="my_polls"),
]
