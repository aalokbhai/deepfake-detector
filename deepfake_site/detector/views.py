import os
import uuid
from datetime import timedelta

import torch
from torchvision import transforms
from PIL import Image
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from django.utils import timezone

from .forms import ImageUploadForm
from .cnn_model import DeepfakeCNN
from .gradcam import GradCAM, overlay_heatmap
from .models import PredictionHistory

# Model load karo (server start hote hi ek baar load hoga)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = DeepfakeCNN().to(device)
model_path = os.path.join(os.path.dirname(__file__), "model_checkpoint.pth")
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

# Grad-CAM object banao (last conv layer use karke)
gradcam = GradCAM(model, model.conv4)

# Same transform jo training ke time use kiya tha
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Privacy: uploaded photos + their heatmaps are auto-deleted after this many
# days so the public demo doesn't accumulate people's faces indefinitely.
RETENTION_DAYS = 7

# Abuse protection: caps how many scans one visitor (by session) can run
# per hour, so a free-tier server can't be hammered into unusable / costly.
RATE_LIMIT_PER_HOUR = 15


def _ensure_session(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _cleanup_old_scans():
    """Delete scan records + their image files older than RETENTION_DAYS.
    Runs opportunistically on each request instead of needing a cron job
    (works fine on free-tier hosts that don't offer scheduled tasks)."""
    cutoff = timezone.now() - timedelta(days=RETENTION_DAYS)
    old_records = PredictionHistory.objects.filter(created_at__lt=cutoff)
    for record in old_records:
        for rel_url in (record.original_image, record.heatmap_image):
            if not rel_url:
                continue
            filename = rel_url.rsplit("/", 1)[-1]
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    old_records.delete()


def _rate_limited(session_key):
    cache_key = f"scan_count:{session_key}"
    count = cache.get(cache_key, 0)
    if count >= RATE_LIMIT_PER_HOUR:
        return True
    cache.set(cache_key, count + 1, timeout=60 * 60)
    return False


def predict_image(request):
    result = None
    confidence = None
    uploaded_image_url = None
    heatmap_url = None
    error = None

    session_key = _ensure_session(request)
    _cleanup_old_scans()

    if request.method == "POST":
        if _rate_limited(session_key):
            error = "Too many scans from this session — please wait a bit before trying again."
            form = ImageUploadForm()
        else:
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                image_file = form.cleaned_data["image"]

                # Save with a random filename — never trust/store the original
                # filename as-is (it can leak personal info, e.g. "WhatsApp
                # Image ... .jpeg", and avoids collisions/path issues).
                ext = image_file.name.rsplit(".", 1)[-1].lower()
                safe_name = f"{uuid.uuid4().hex}.{ext}"

                fs = FileSystemStorage()
                try:
                    filename = fs.save(safe_name, image_file)
                    uploaded_image_url = fs.url(filename)

                    img = Image.open(image_file).convert("RGB")
                    img_tensor = transform(img).unsqueeze(0).to(device)
                    img_tensor.requires_grad_(True)

                    output = model(img_tensor)
                    probs = torch.softmax(output, dim=1)
                    pred_class = torch.argmax(probs, dim=1).item()
                    confidence = round(probs[0][pred_class].item() * 100, 2)
                    result = "Real" if pred_class == 1 else "Fake"

                    cam = gradcam.generate(img_tensor, pred_class)

                    heatmap_filename = "heatmap_" + filename
                    original_path = os.path.join(fs.location, filename)
                    heatmap_path = os.path.join(fs.location, heatmap_filename)
                    overlay_heatmap(cam, original_path, heatmap_path)
                    heatmap_url = fs.url(heatmap_filename)

                    PredictionHistory.objects.create(
                        original_image=uploaded_image_url,
                        heatmap_image=heatmap_url,
                        result=result,
                        confidence=confidence,
                        session_key=session_key,
                    )
                except Exception:
                    error = "Couldn't analyze that image. Please try a different photo."
    else:
        form = ImageUploadForm()

    return render(request, "detector/upload.html", {
        "form": form,
        "result": result,
        "confidence": confidence,
        "uploaded_image_url": uploaded_image_url,
        "heatmap_url": heatmap_url,
        "error": error,
        "retention_days": RETENTION_DAYS,
    })


def history_view(request):
    session_key = _ensure_session(request)
    _cleanup_old_scans()

    # Privacy: only ever show the CURRENT visitor's own scans, never anyone
    # else's uploaded photos.
    records = PredictionHistory.objects.filter(session_key=session_key).order_by('-created_at')
    total = records.count()
    real_count = records.filter(result="Real").count()
    fake_count = records.filter(result="Fake").count()
    return render(request, "detector/history.html", {
        "records": records,
        "total": total,
        "real_count": real_count,
        "fake_count": fake_count,
        "retention_days": RETENTION_DAYS,
    })
