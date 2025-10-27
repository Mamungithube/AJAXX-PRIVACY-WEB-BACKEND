from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
router = DefaultRouter() 
router.register(r'api/Product-all', views.ProductViewSet,basename='product')
urlpatterns = [
    path('', include(router.urls)),
]