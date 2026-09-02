from django.db import models


class PredictionHistory(models.Model):
    original_image = models.CharField(max_length=255)
    heatmap_image = models.CharField(max_length=255)
    result = models.CharField(max_length=10)
    confidence = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Privacy: ties a scan to the visitor's browser session so the public
    # "Scan History" page only ever shows a person their OWN uploads, never
    # other visitors' photos. No accounts/login needed for this.
    session_key = models.CharField(max_length=40, blank=True, default="", db_index=True)

    def __str__(self):
        return f"{self.result} ({self.confidence}%) - {self.created_at}"
