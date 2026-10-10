from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import RegisterForm, LoginForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Aramıza hoş geldin, @{user.username}! Hesabın oluşturuldu.")
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    redirect_to = request.POST.get("next") or request.GET.get("next") or ""

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Tekrar hoş geldin, @{user.username}!")

            # Güvenli URL yönlendirmesi
            if redirect_to and url_has_allowed_host_and_scheme(
                url=redirect_to,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(redirect_to)
            return redirect("home")
    else:
        form = LoginForm(request)

    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": redirect_to},
    )


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Oturumun başarıyla kapatıldı. Görüşmek üzere!")
    return redirect("home")
