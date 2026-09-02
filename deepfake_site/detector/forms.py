from django import forms
from django.conf import settings
from PIL import Image, UnidentifiedImageError

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageUploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data["image"]

        # 1) Size limit — protects a free-tier server from being overwhelmed
        max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 5 * 1024 * 1024)
        if image.size > max_bytes:
            raise forms.ValidationError(
                f"Image is too large ({image.size // (1024*1024)}MB). Max allowed is "
                f"{max_bytes // (1024*1024)}MB."
            )

        # 2) Extension whitelist
        ext = image.name.rsplit(".", 1)[-1].lower() if "." in image.name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Only JPG, PNG, or WEBP images are allowed.")

        # 3) Declared content-type check
        if image.content_type not in ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError("Unsupported file type.")

        # 4) Actually verify the bytes are a real, undamaged image (Django's
        # ImageField already does a light check, but we double-verify here to
        # guard against corrupted or disguised files reaching the model).
        try:
            image.seek(0)
            img = Image.open(image)
            img.verify()
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError("This file isn't a valid image.")
        finally:
            image.seek(0)

        return image
