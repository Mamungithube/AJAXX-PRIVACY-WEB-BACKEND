from django.urls import path
from .views import PrivacyInfoView

urlpatterns = [
    path("optery/privacy/<str:email>/", PrivacyInfoView.as_view(), name="privacy-info"),
]
