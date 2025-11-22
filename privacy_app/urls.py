from django.urls import path
from . import views

urlpatterns = [
    path("api/get_databrokers_list/", views.get_databrokers_list, name="get-brokers-list"),
    path("optery/scans/", views.get_optouts, name="get-scans"),
    path("optery/custom-removals/", views.get_custom_removals, name="get-custom-removals"),
    path("optery/webhook/", views.optery_webhook, name="optery_webhook"),
    path("members/", views.AddMemberAPIView.as_view(), name="member"),
]
