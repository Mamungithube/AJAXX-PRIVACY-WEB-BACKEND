from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
router = DefaultRouter() 
router.register('review', views.ReviewViewset)
router.register('ContactUs', views.ContactusViewset) 
router.register('faq',views.FAQListViewset,basename='Faq')
urlpatterns = [
    path('', include(router.urls)),
]