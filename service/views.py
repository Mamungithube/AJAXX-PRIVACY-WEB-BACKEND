
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from . import models, serializers
from rest_framework import permissions

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # ✅ GET, HEAD, OPTIONS →(anonymous user)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # ✅ POST, PUT, PATCH, DELETE → authenticated user
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # ✅ Read → all users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # ✅ DELETE → Admin Or Owner
        if request.method == 'DELETE':
            return request.user.is_staff or obj.reviewer == request.user
        
        # ✅ PUT/PATCH → only Owner
        return obj.reviewer == request.user


"""------------------Contact Us related views-------------------"""

class ContactusViewset(viewsets.ModelViewSet):
    queryset = models.ContactUs.objects.all()
    serializer_class = serializers.ContactUsSerializer


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            
            email = serializer.validated_data.get('email')
            subject = serializer.validated_data.get('Subject')
            message = serializer.validated_data.get('Description')

            send_mail(
                subject=f"New Contact Message for Ajaxxdatascrubber.com: {subject}",
                message=f"From: {email}\n\nHI craig,\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["craigcrisp@fortress-apps.com"],
                fail_silently=False,
            )

            return Response({'message': 'Message sent successfully!'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




"""-----------------------Review related views-----------------------"""


class ReviewViewset(viewsets.ModelViewSet):
    queryset = models.Review.objects.all()
    serializer_class = serializers.ReviewSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]  # ✅ Custom permission

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]  # Anyone can view
        return [IsOwnerOrAdminOrReadOnly()]  # Custom permission for rest
    
    
    # ✅ List API with Search + Pagination + ?all=true support
    def list(self, request, *args, **kwargs):
        reviews = models.Review.objects.all().order_by('-created')  # Latest first

        search = request.GET.get('search')
        show_all = request.GET.get('all', 'false').lower() == 'true'

        # 🔍 Search
        if search:
            reviews = reviews.filter(
                Q(body__icontains=search) |
                Q(reviewer__email__icontains=search) |
                Q(reviewer__Fullname__icontains=search)
            )

        # ✅ If ?all=true → no pagination
        if show_all:
            serializer = self.get_serializer(reviews, many=True)
            return Response({
                "total": reviews.count(),
                "results": serializer.data
            })

        # ✅ Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        total_reviews = reviews.count()
        start = (page - 1) * page_size
        end = start + page_size

        paginated = reviews[start:end]
        serializer = self.get_serializer(paginated, many=True)

        return Response({
            "total": total_reviews,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_reviews + page_size - 1) // page_size,
            "results": serializer.data
        })

    # ✅ POST Create - Auto assign logged-in user as reviewer
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

    # ✅ PUT Update
    def update(self, request, *args, **kwargs):
        instance = self.get_object()   
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ✅ PATCH Partial Update
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()      
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ✅ DELETE - Admin or Owner can delete
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )