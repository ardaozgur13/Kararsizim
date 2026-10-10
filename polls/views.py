from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home_view(request):
    """
    Anasayfa anket akışı.
    Aşama 0 ve 1 için boş durum (empty-state) veya hoş geldiniz arayüzü sunar.
    """
    polls = []  # Aşama 2'de Poll modeli eklendiğinde queryset bağlanacaktır.
    return render(request, "polls/home.html", {"polls": polls})


@login_required
def create_poll_view(request):
    """
    Anket oluşturma (Aşama 2'de tam form ve model doğrulamalarıyla geliştirilecektir).
    """
    return render(request, "polls/create.html")


@login_required
def my_polls_view(request):
    """
    Kullanıcının kendi anketleri (Aşama 2'de listelenecektir).
    """
    return render(request, "polls/home.html", {"polls": []})
