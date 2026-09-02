from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.static import serve as serve_static_file

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("detector.urls")),
]

# Serve uploaded photos + generated heatmaps.
# Note: Django's built-in `static()` helper only works when DEBUG=True, but
# this app has no separate object-storage (S3/Cloudinary) configured, so we
# serve media directly even in production. That's fine for a small,
# single-instance academic/demo deployment like this one; for a larger-scale
# production app you'd move media to S3/Cloudinary instead.
urlpatterns += [
    path(
        f"{settings.MEDIA_URL.strip('/')}/<path:path>",
        serve_static_file,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
