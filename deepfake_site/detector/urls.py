from django.urls import path
from . import views

urlpatterns = [
    path("", views.predict_image, name="predict_image"),
    path("history/", views.history_view, name="history"),
]