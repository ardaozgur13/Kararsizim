from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Poll
from .forms import PollCreateForm


def home_view(request):
    """
    Anasayfa anket akışı: En yeni anketler üstte, sayfa başına 10 anket, sayfalama ile.
    N+1 sorgularını önlemek için select_related('author') ve prefetch_related('options') kullanılır.
    """
    polls_list = (
        Poll.objects.select_related("author")
        .prefetch_related("options")
        .all()
    )
    paginator = Paginator(polls_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "polls/home.html",
        {"page_obj": page_obj, "polls": page_obj.object_list},
    )


def poll_detail_view(request, poll_id):
    """
    Anket detay sayfası: Anketi, seçenekleri ve yazar bilgisini gösterir.
    (Oy verme mekanizması Aşama 3'te eklenecektir).
    """
    poll = get_object_or_404(
        Poll.objects.select_related("author").prefetch_related("options"),
        pk=poll_id,
    )
    return render(request, "polls/detail.html", {"poll": poll})


@login_required
def create_poll_view(request):
    """
    Anket oluşturma: Sadece giriş yapmış kullanıcılar içindir.
    En az 2, en fazla 5 seçenek girilebilir.
    """
    if request.method == "POST":
        form = PollCreateForm(request.POST)
        if form.is_valid():
            poll = form.save(author=request.user)
            messages.success(request, "Anketin başarıyla paylaşıldı! Fikirler gelmeye başlasın.")
            return redirect("poll_detail", poll_id=poll.id)
        # Form geçersizse kullanıcının yazdığı seçenekleri koru
        submitted_options = request.POST.getlist("options")
    else:
        form = PollCreateForm()
        submitted_options = ["", ""]  # Başlangıçta 2 boş seçenek alanı

    return render(
        request,
        "polls/create.html",
        {
            "form": form,
            "submitted_options": submitted_options,
        },
    )


@login_required
@require_POST
def delete_poll_view(request, poll_id):
    """
    Anket silme: Yalnızca anket sahibi silebilir (backend yetki kontrollü).
    """
    poll = get_object_or_404(Poll, pk=poll_id)
    if poll.author != request.user:
        return HttpResponseForbidden("Bu anketi silme yetkiniz bulunmuyor.")

    poll.delete()
    messages.success(request, "Anket başarıyla silindi.")

    # Eğer istek kullanıcının kendi profilinden geldiyse oraya, aksi halde anasayfaya dön
    referer = request.META.get("HTTP_REFERER", "")
    if "profilim" in referer:
        return redirect("my_polls")
    return redirect("home")


@login_required
def my_polls_view(request):
    """
    Kullanıcının kendi oluşturduğu anketlerin listesi.
    """
    my_polls_list = (
        Poll.objects.filter(author=request.user)
        .prefetch_related("options")
        .all()
    )
    paginator = Paginator(my_polls_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "polls/my_polls.html",
        {"page_obj": page_obj, "polls": page_obj.object_list},
    )
