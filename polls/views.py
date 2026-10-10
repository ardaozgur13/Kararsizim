import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count
from django.db import IntegrityError

from .models import Poll, Option, Vote
from .forms import PollCreateForm


def get_user_voted_option(poll, request):
    """
    Kullanıcının veya ziyaretçinin (session) bu ankete daha önce oy verip vermediğini döner.
    """
    if request.user.is_authenticated:
        vote = Vote.objects.filter(poll=poll, user=request.user).select_related("option").first()
    else:
        session_key = request.session.session_key
        if not session_key:
            return None
        vote = Vote.objects.filter(poll=poll, session_key=session_key).select_related("option").first()
    return vote.option if vote else None


def get_poll_results_data(poll, user_voted_option_id=None):
    """
    Anket seçeneklerinin oy dağılımını, yüzdelerini ve toplam oy sayısını hesaplar.
    N+1 sorgularını önlemek için annotate(votes_count=Count('votes')) kullanır.
    """
    options_with_votes = (
        poll.options.annotate(votes_count=Count("votes"))
        .order_by("position", "id")
    )
    total_votes = poll.votes.count()

    options_data = []
    for opt in options_with_votes:
        count = opt.votes_count
        pct = round((count / total_votes) * 100) if total_votes > 0 else 0
        options_data.append({
            "id": opt.id,
            "text": opt.text,
            "votes_count": count,
            "percentage": pct,
            "is_selected": (opt.id == user_voted_option_id),
        })

    return {
        "total_votes": total_votes,
        "options": options_data,
        "user_voted_option_id": user_voted_option_id,
    }


def home_view(request):
    """
    Anasayfa anket akışı: En yeni üstte, 10'arlık sayfalama.
    N+1 sorgularını önlemek için author, options ve toplam oy annotate edilir.
    """
    polls_list = (
        Poll.objects.select_related("author")
        .prefetch_related("options")
        .annotate(total_votes_count=Count("votes"))
        .order_by("-created_at")
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
    Anket detay sayfası:
    - Oy vermişse doğrudan sonuçları gösterir.
    - Oy vermemişse oy verme formunu gösterir (istenirse 'sonuclar=1' ile sonuçlara bakılabilir).
    """
    poll = get_object_or_404(
        Poll.objects.select_related("author").prefetch_related("options"),
        pk=poll_id,
    )

    user_voted_option = get_user_voted_option(poll, request)
    user_voted_option_id = user_voted_option.id if user_voted_option else None

    # Kullanıcı oy verdiyse veya 'sonuclar=1' parametresiyle geldiyse sonuçları göster
    view_results_only = request.GET.get("sonuclar") == "1"
    show_results = (user_voted_option is not None) or view_results_only

    results_data = get_poll_results_data(poll, user_voted_option_id)

    return render(
        request,
        "polls/detail.html",
        {
            "poll": poll,
            "user_voted_option": user_voted_option,
            "show_results": show_results,
            "results_data": results_data,
            "view_results_only": view_results_only,
        },
    )


@require_POST
def vote_poll_view(request, poll_id):
    """
    Oy verme endpoint'i:
    - Hem fetch (JSON) hem de klasik HTML form POST isteklerini destekler.
    - Üyeler user, ziyaretçiler session_key ile oy verir.
    - Aynı ankete birden fazla oy engellenir ("Bu ankete zaten oy verdin.").
    - Başka anketin seçeneğiyle oy verilemez.
    """
    poll = get_object_or_404(Poll, pk=poll_id)
    is_ajax = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("Accept", "")
    )

    # Seçenek ID'sini al (form data veya json)
    option_id = request.POST.get("option_id")
    if not option_id and request.body:
        try:
            body_data = json.loads(request.body)
            option_id = body_data.get("option_id")
        except json.JSONDecodeError:
            pass

    if not option_id:
        err_msg = "Lütfen oy vermek için bir seçenek belirleyin."
        if is_ajax:
            return JsonResponse({"success": False, "error": err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect("poll_detail", poll_id=poll.id)

    # Seçeneğin bu ankete ait olup olmadığını doğrula
    option = Option.objects.filter(pk=option_id, poll=poll).first()
    if not option:
        err_msg = "Geçersiz bir seçenek belirttiniz."
        if is_ajax:
            return JsonResponse({"success": False, "error": err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect("poll_detail", poll_id=poll.id)

    # Çift oy kontrolü
    if request.user.is_authenticated:
        already_voted = Vote.objects.filter(poll=poll, user=request.user).exists()
    else:
        session_key = request.session.session_key
        already_voted = (
            Vote.objects.filter(poll=poll, session_key=session_key).exists()
            if session_key
            else False
        )

    if already_voted:
        err_msg = "Bu ankete zaten oy verdin."
        if is_ajax:
            return JsonResponse({"success": False, "error": err_msg}, status=400)
        messages.warning(request, err_msg)
        return redirect("poll_detail", poll_id=poll.id)

    # Oyu kaydet
    try:
        if request.user.is_authenticated:
            Vote.objects.create(poll=poll, option=option, user=request.user)
        else:
            if not request.session.session_key:
                request.session.save()
            Vote.objects.create(
                poll=poll,
                option=option,
                session_key=request.session.session_key,
            )
    except IntegrityError:
        err_msg = "Bu ankete zaten oy verdin."
        if is_ajax:
            return JsonResponse({"success": False, "error": err_msg}, status=400)
        messages.warning(request, err_msg)
        return redirect("poll_detail", poll_id=poll.id)

    # Başarılı yanıt
    if is_ajax:
        results = get_poll_results_data(poll, user_voted_option_id=option.id)
        return JsonResponse({"success": True, **results})

    messages.success(request, "Oyun başarıyla kaydedildi!")
    return redirect("poll_detail", poll_id=poll.id)


@login_required
def create_poll_view(request):
    """
    Anket oluşturma: Sadece giriş yapmış kullanıcılar içindir.
    """
    if request.method == "POST":
        form = PollCreateForm(request.POST)
        if form.is_valid():
            poll = form.save(author=request.user)
            messages.success(request, "Anketin başarıyla paylaşıldı! Fikirler gelmeye başlasın.")
            return redirect("poll_detail", poll_id=poll.id)
        submitted_options = request.POST.getlist("options")
    else:
        form = PollCreateForm()
        submitted_options = ["", ""]

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
        .annotate(total_votes_count=Count("votes"))
        .order_by("-created_at")
    )
    paginator = Paginator(my_polls_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "polls/my_polls.html",
        {"page_obj": page_obj, "polls": page_obj.object_list},
    )
