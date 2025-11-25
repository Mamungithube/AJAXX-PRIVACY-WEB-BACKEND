from django.urls import path
from . import views

urlpatterns = [
    # path("api/get_databrokers_list/", views.get_databrokers_list, name="get-brokers-list"),
    # path("optery/scans/", views.get_optouts, name="get-scans"),
    # path("optery/custom-removals/", views.get_custom_removals, name="get-custom-removals"),
    # path("optery/webhook/", views.optery_webhook, name="optery_webhook"),
    # path("optery/add-member/", views.AddOpteryMember.as_view()),
    path('optery/members/', views.create_optery_member, name='create_optery_member'),
    path('api/optery/members/cbv/', views.OpteryMemberView.as_view(), name='optery_member_cbv'),
    path('optery/data-scans/', views.OpteryCombinedView.as_view(), name='optery-combined'),
    path("optery/history/", views.OpteryHistoryListView.as_view()),

    path("optery/custom-removals/", views.CustomRemovalListView.as_view()),
    path("custom-removal/", views.CustomRemovalCreateView.as_view()),
]
