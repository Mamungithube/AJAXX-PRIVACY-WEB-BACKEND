from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from . import models, serializers

class ContactusViewset(viewsets.ModelViewSet):
    queryset = models.ContactUs.objects.all()
    serializer_class = serializers.ContactUsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # ইমেইল পাঠানো
            email = serializer.validated_data.get('email')
            subject = serializer.validated_data.get('Subject')
            message = serializer.validated_data.get('Description')

            send_mail(
                subject=f"New Contact Message: {subject}",
                message=f"From: {email}\n\nMessage:\n{message}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )

            return Response({'message': 'Message sent successfully!'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class ReviewViewset(viewsets.ModelViewSet):
    queryset = models.Review.objects.all()
    serializer_class = serializers.ReviewSerializer
    permission_classes = [IsAuthenticated]

    # ✅ Pagination + Filtering + Search
    def list(self, request, *args, **kwargs):
        reviews = models.Review.objects.all()

        # 🔍 Query parameters
        search = request.GET.get('search')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # Optional search (for example: by title or content)
        if search:
            reviews = reviews.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(user__username__icontains=search)
            )

        # ✅ Pagination logic
        total_reviews = reviews.count()
        start = (page - 1) * page_size
        end = start + page_size
        paginated_reviews = reviews[start:end]

        serializer = self.get_serializer(paginated_reviews, many=True)

        return Response({
            "total": total_reviews,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_reviews + page_size - 1) // page_size,
            "results": serializer.data
        })

    # ✅ সম্পূর্ণ রিভিউ আপডেট (PUT)
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ✅ আংশিক আপডেট (PATCH)
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
