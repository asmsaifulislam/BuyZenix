from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from orders.models import Order
from .forms import UserProfileForm, UserRegistrationForm, UserUpdateForm
from .models import UserProfile


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by("-created")[:5]
    return render(request, "accounts/dashboard.html", {"orders": orders})


@login_required
def profile_edit(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        uform = UserUpdateForm(request.POST, instance=request.user)
        pform = UserProfileForm(request.POST, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            return redirect("accounts:dashboard")
    else:
        uform = UserUpdateForm(instance=request.user)
        pform = UserProfileForm(instance=profile)
    return render(
        request, "accounts/profile_edit.html", {"uform": uform, "pform": pform}
    )


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created")
    return render(request, "accounts/order_history.html", {"orders": orders})
