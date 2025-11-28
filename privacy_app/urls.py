from django.urls import path
from . import views

urlpatterns = [
    path('optery/members/', views.create_optery_member, name='create_optery_member'),
    # path('api/optery/members/cbv/', views.OpteryMemberView.as_view(), name='optery_member_cbv'),
    path('optery/data-scans/', views.OpteryCombinedView.as_view(), name='optery-combined'),
    path("optery/history/", views.OpteryHistoryListView.as_view()),

    path("optery/custom-removals/", views.CustomRemovalListView.as_view()),
    path("custom-removal/", views.CustomRemovalCreateView.as_view()),
    path('api/optery-members/<str:uuid_str>/', views.get_optery_member_by_uuid, name='get_optery_member_by_uuid'),
]
