from .models import Product
from .serializers import ProductSerializer
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS

class IsAuthenticatedOrAdminOnly(BasePermission):
    def has_permission(self, request, view):
        # Allow read-only access (GET, HEAD, OPTIONS) to any authenticated user
        if request.method in SAFE_METHODS:
            return IsAuthenticated().has_permission(request, view)
        
        # For write actions (POST, PUT, DELETE), only allow staff members (admins)
        return bool(request.user and request.user.is_staff)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrAdminOnly]
