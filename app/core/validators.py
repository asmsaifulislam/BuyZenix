import os
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
    ".webp", ".heic", ".heif", ".avif", ".svg", ".ico",
    ".jfif", ".jpe", ".apng",
}

ALLOWED_IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/bmp",
    "image/tiff", "image/webp", "image/heic", "image/heif",
    "image/avif", "image/svg+xml", "image/x-icon", "image/apng",
    "image/jp2", "image/jpx", "image/jpm",
}


def validate_image_file(file_obj):
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image format '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        )
