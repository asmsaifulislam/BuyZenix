from django import forms
from django.contrib.auth.models import User

from core.models import Category, Product, ProductImage, ProductSize
from accounts.models import UserProfile
from .models import Banner, Page, SiteSettings


class SupplierProductForm(forms.ModelForm):
    clear_image = forms.BooleanField(
        required=False, label="Remove current image",
        widget=forms.CheckboxInput(attrs={"class": "form-check"})
    )
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "sale_price", "image", "video_url", "model_3d", "stock", "available", "featured"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "price": forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "placeholder": "Leave empty for no sale"}),
            "video_url": forms.URLInput(attrs={"class": "form-input", "placeholder": "https://youtube.com/watch?v=..."}),
            "model_3d": forms.ClearableFileInput(attrs={"class": "form-input", "accept": ".glb,.gltf"}),
            "stock": forms.NumberInput(attrs={"class": "form-input"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-input", "accept": "image/*,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp,.heic,.heif,.avif,.svg,.ico,.jfif,.apng"}),
            "available": forms.CheckboxInput(attrs={"class": "form-check"}),
            "featured": forms.CheckboxInput(attrs={"class": "form-check"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.image:
            self.fields["clear_image"].initial = False
        else:
            self.fields["clear_image"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("clear_image") and not cleaned.get("image"):
            cleaned["image"] = None
        return cleaned

    def save_gallery(self, product, request):
        files = request.FILES.getlist("gallery_images")
        colors = [c.strip() for c in request.POST.get("gallery_colors", "").split(",") if c.strip()]
        angles = [a.strip() for a in request.POST.get("gallery_angles", "").split(",") if c.strip()]
        labels = [l.strip() for l in request.POST.get("gallery_labels", "").split(",") if l.strip()]

        pos = product.gallery.count()
        for i, f in enumerate(files):
            ProductImage.objects.create(
                product=product,
                image=f,
                color=colors[i] if i < len(colors) else "",
                angle=angles[i] if i < len(angles) else "front",
                label=labels[i] if i < len(labels) else "",
                position=pos + i,
            )

    def save_sizes(self, product, request):
        import json
        raw = request.POST.get("sizes_data", "[]")
        try:
            sizes = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            sizes = []
        ProductSize.objects.filter(product=product).delete()
        for s in sizes:
            name = s.get("name", "").strip()
            if name:
                ProductSize.objects.create(
                    product=product,
                    name=name,
                    is_active=bool(s.get("active", True)),
                )


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_staff", "is_active"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
        }


class UserProfileRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["role", "company_name", "phone", "address_line1", "city", "state", "country"]
        widgets = {
            "role": forms.Select(attrs={"class": "form-input"}),
            "company_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "address_line1": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
            "state": forms.TextInput(attrs={"class": "form-input"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ["title", "image", "link_url", "is_active", "position"]


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "slug", "content", "meta_description", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "slug": forms.TextInput(attrs={"class": "form-input"}),
            "content": forms.Textarea(attrs={"class": "form-input", "rows": 10}),
            "meta_description": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["site_name", "site_tagline", "contact_email", "contact_phone", "address", "facebook_url", "twitter_url", "instagram_url", "logo"]
        widgets = {
            "site_name": forms.TextInput(attrs={"class": "form-input"}),
            "site_tagline": forms.TextInput(attrs={"class": "form-input"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-input"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-input"}),
            "address": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }
