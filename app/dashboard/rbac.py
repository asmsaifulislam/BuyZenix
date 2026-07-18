from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import Group, Permission
from django.shortcuts import get_object_or_404, redirect, render
from django import forms


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-input"})}


@staff_member_required
def rbac_groups(request):
    """List all permission groups."""
    groups = Group.objects.annotate(user_count__count=Count("user")).order_by("name")
    return render(request, "dashboard/admin_rbac.html", {"groups": groups})


from django.db.models import Count


@staff_member_required
def rbac_group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            perms = request.POST.getlist("permissions")
            group.permissions.set(perms)
            messages.success(request, f"Group '{group.name}' created.")
            return redirect("dashboard:rbac_groups")
    else:
        form = GroupForm()
    permissions = Permission.objects.select_related("content_type").order_by("content_type__model", "codename")
    return render(request, "dashboard/admin_rbac_form.html", {"form": form, "action": "Create", "permissions": permissions, "selected_perms": []})


@staff_member_required
def rbac_group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            group = form.save()
            perms = request.POST.getlist("permissions")
            group.permissions.set(perms)
            messages.success(request, f"Group '{group.name}' updated.")
            return redirect("dashboard:rbac_groups")
    else:
        form = GroupForm(instance=group)
    permissions = Permission.objects.select_related("content_type").order_by("content_type__model", "codename")
    selected_perms = list(group.permissions.values_list("id", flat=True))
    return render(request, "dashboard/admin_rbac_form.html", {
        "form": form, "action": "Edit", "group": group,
        "permissions": permissions, "selected_perms": selected_perms,
    })


@staff_member_required
def rbac_group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        name = group.name
        group.delete()
        messages.success(request, f"Group '{name}' deleted.")
        return redirect("dashboard:rbac_groups")
    return render(request, "dashboard/admin_rbac_delete.html", {"group": group})
