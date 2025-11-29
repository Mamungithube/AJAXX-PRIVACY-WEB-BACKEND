from django.urls import path
from . import views

urlpatterns = [
    path('optery/members/', views.CreateOpteryMember.as_view(), name='create_optery_member'),
    # path('api/optery/members/cbv/', views.OpteryMemberView.as_view(), name='optery_member_cbv'),
    path('optery/data-scans/', views.OpteryCombinedView.as_view(), name='optery-combined'),
    path("optery/history/<str:email_str>/", views.OpteryHistoryListView.as_view()),

    path("optery/custom-removals/", views.CustomRemovalListView.as_view()),
    path("custom-removal/", views.CustomRemovalCreateView.as_view()),
    path('api/optery-members/<str:email_str>/', views.get_optery_member_by_email, name='get_optery_member_by_email'),
]
