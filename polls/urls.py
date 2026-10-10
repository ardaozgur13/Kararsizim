from django.urls import path
from .views import (
    home_view,
    poll_detail_view,
    vote_poll_view,
    create_poll_view,
    delete_poll_view,
    my_polls_view,
)

urlpatterns = [
    path("", home_view, name="home"),
    path("anket/yeni/", create_poll_view, name="create_poll"),
    path("anket/<int:poll_id>/", poll_detail_view, name="poll_detail"),
    path("anket/<int:poll_id>/oy/", vote_poll_view, name="vote_poll"),
    path("anket/<int:poll_id>/sil/", delete_poll_view, name="delete_poll"),
    path("profilim/", my_polls_view, name="my_polls"),
]
