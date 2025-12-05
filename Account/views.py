from re import search
import requests
from rest_framework import (
    generics, 
    permissions, 
    status
)
from .serializers import (
    UserSerializer, 
    RegistrationSerializer, 
    LoginSerializer, 
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    GoogleAuthSerializer
)
from .models import Profile
from rest_framework import viewsets
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives,send_mail
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login
from django.shortcuts import get_object_or_404
from .utils import generate_otp
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth import get_user_model
from rest_framework import status
from django.db.models import Q  # For search
from rest_framework.decorators import action

from django.core.mail import EmailMessage
User = get_user_model()

from .google_auth import get_or_create_google_user, generate_jwt_for_user
import requests

class UserAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)

        users = User.objects.all()

        # Query params
        email = request.GET.get('email')
        search = request.GET.get('search')

        if email:
            users = users.filter(email__icontains=email)

        if search:
            users = users.filter(
                Q(Fullname__icontains=search) |
                Q(email__icontains=search)
            )

        # ✅ Pagination parameters
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size
        paginated_users = users[start:end]

        serializer = UserSerializer(paginated_users, many=True)
        total_users = users.count()

        return Response({
            'total': total_users,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_users + page_size - 1) // page_size,
            'results': serializer.data
        })

    def post(self, request):
        is_many = isinstance(request.data, list)
        serializer = UserSerializer(data=request.data, many=is_many)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



""" ----------------Gooooooooooogle auth  view------------------- """


class GoogleLoginAPIView(APIView):
    """
    Receives Google id_token from frontend and returns JWT tokens.
    """
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get user
        user = serializer.create_or_login_user()
        
        # ✅ AUTO DJANGO ACTIVE - Session Login
        login(request, user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": user.email,
                "name": user.Fullname,
                "id": user.id
            }
        }, status=status.HTTP_200_OK)


""" ----------------registration view------------------- """
class RegisterAPIView(APIView):
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Serializer এ সব কাজ হয়ে যাচ্ছে
            
            return Response({
                'detail': 'Registration successful! Check your email for OTP verification.',
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



""" ----------------again send OTP API view------------------- """

class ResendOTPApiView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        user = get_object_or_404(User, email=email)

        otp_code = generate_otp()
        user.profile.otp = otp_code
        user.profile.save()

        html_content = render_to_string('send_code.html', {'otp': otp_code, 'user': user})

        try:
            msg = EmailMessage(
                subject='Your New Code',  # Email Subject
                body=html_content,  
                from_email='9cdbfd001@smtp-brevo.com', # Use settings.DEFAULT_FROM_EMAIL or a hardcoded email
                to=[email],  # Recipient list
            )
            msg.content_subtype = "html" 
            msg.send()

            return Response({'Message': 'OTP Has Been Resent To Your Email'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            
            return Response({'Error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





""" ----------------verify OTP API view------------------- """
class VerifyOTPApiView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp = request.data.get('otp')

        user = get_object_or_404(User, email=email)
        profile = user.profile

        if profile.otp == otp:
            user.is_active = True
            user.save(update_fields=['is_active'])
            profile.otp = None
            profile.save(update_fields=['otp'])
            return Response({'Message': 'Account Activate Successfully'}, status=status.HTTP_200_OK)
        return Response({'Error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)



""" ----------------Login view------------------- """
from rest_framework.permissions import AllowAny

class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    return Response(
                        {'error': 'Account not activated. Verify OTP first!'},
                        status=status.HTTP_403_FORBIDDEN
                    )

                login(request, user)

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'Fullname': user.Fullname,
                        'is_staff': user.is_staff,
                    }
                }, status=status.HTTP_200_OK)

            return Response(
                {'error': 'Email and password do not match'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BaseResponseMixin:
    def success_response(self, message, data=None, status_code=status.HTTP_200_OK):
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        return Response(response, status=status_code)

    def error_response(self, message, data=None, status_code=status.HTTP_400_BAD_REQUEST):
        response = {
            "success": False,
            "message": message,
            "data": data
        }
        return Response(response, status=status_code)



""" ----------------Logout view------------------- """

class LogoutAPIView(BaseResponseMixin, generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            # Debugging line to check the token
            print(f"Received refresh token: {refresh_token}")
            if not refresh_token:
                return self.error_response(
                    message="Refresh token is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            # Debugging line to check the token
            print(f"Token before blacklisting: {token}")
            token.blacklist()

            return self.success_response(
                message="Logged out successfully",
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return self.error_response(
                message="Invalid or expired refresh token",
                status_code=status.HTTP_400_BAD_REQUEST,
            )



""" ----------------Forgot Password view------------------- """

class ForgotPasswordAPIView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'detail': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            user.set_password(password)
            user.save()

            return Response({'detail': 'Password has been reset successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





""" ----------------Total User Count view------------------- """

class TotalUserCountView(APIView):
    permission_classes = [IsAdminUser]  #  restrict to admin only
    # permission_classes = [IsAuthenticated]


    def get(self, request):
        total_users = User.objects.count()
        return Response({"total_users": total_users})



""" ----------------Account Delete view------------------- """

class AdminDeleteUserView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({'detail': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)



""" ---------------------Admin Check view-------------------------- """

class IsAdminCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_admin = request.user.is_staff or request.user.is_superuser
        return Response({
            "email": request.user.email,
            "Fullname": request.user.Fullname,
            "is_admin": is_admin
        })


""" ------------------------Profile Detail view--------------------------- """

class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Get or create profile for the current user
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
""" -------------------Profile Update view----------------------- """

class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Get or create profile for the current user
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile  

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full profile data after update
        profile_serializer = ProfileSerializer(instance)
        return Response(profile_serializer.data)
    

""" -------------------Change Password view----------------------- """

class ChangePasswordViewSet(viewsets.GenericViewSet):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated] 

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:  
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user
        serializer = self.get_serializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"message": "Password changed successfully!"}, status=status.HTTP_204_NO_CONTENT)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

""" -------------------User Block view----------------------- """



class UserBlockViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser] 

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        try:
            user_to_block = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if user_to_block == request.user:
            return Response(
                {"detail": "You cannot block your own admin account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_to_block.is_active = False
        user_to_block.save()
        
        return Response(
            {"detail": f"Block successfully Done"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        try:
            user_to_unblock = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user_to_unblock.is_active = True
        user_to_unblock.save()
        
        return Response(
            {"detail": f"UnBlock successfully Done"},
            status=status.HTTP_200_OK
        )
