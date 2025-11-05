from django.urls import path
from . import views

urlpatterns = [
    path("api/get_databrokers_list/", views.get_databrokers_list, name="get-brokers-list"),
]
