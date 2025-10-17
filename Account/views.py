from rest_framework import (
    generics, 
    permissions, 
    status
)
from .serializers import (
    UserSerializer, 
    RegistrationSerializer, 
    LoginSerializer, 
    UserLoginSerializer, 
    ResetPasswordSerializer,
    # GoogleAuthSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer
)
from .models import Profile

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

from django.core.mail import EmailMessage
User = get_user_model()

# user view 
class UserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk:
            user = get_object_or_404(User, pk=pk)
            serializer = UserSerializer(user)
        else:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# """ ----------------Gooooooooooogle auth  view------------------- """



# class GoogleLoginView(generics.GenericAPIView):
#     serializer_class = GoogleAuthSerializer
#     permission_classes = [permissions.AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user = serializer.create_or_login_user()
#         refresh = RefreshToken.for_user(user)

#         return Response({
#             "refresh": str(refresh),
#             "access": str(refresh.access_token),
#             "user": {
#                 "email": user.email,
#                 "fullname": user.Fullname,
#                 "provider": user.social_auth_provider,
#                 "profile_picture": user.profile.profile_picture.url if user.profile.profile_picture else None,
#             }
#         }, status=status.HTTP_200_OK)





""" ----------------registration view------------------- """
class RegisterAPIView(APIView):
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            profile.otp = generate_otp()
            profile.save()

            email_subject = 'Welcome To Our Platform!'
            email_body = render_to_string(
                'welcome_email.html', {'Fullname': user.Fullname})

            email = EmailMultiAlternatives(
                email_subject, '', 'mdmamun340921@gmail.com', [user.email])
            email.attach_alternative(email_body, 'text/html')
            email.send()

            return Response({'detail': 'Check your email for confirmation'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


""" ----------------again send OTP API view------------------- """




class ResendOTPApiView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        
        # 1. Validate user existence
        user = get_object_or_404(User, email=email)

        # 2. Generate and save the new OTP
        otp_code = generate_otp()
        user.profile.otp = otp_code
        user.profile.save()

        # 3. Render the HTML template
        # The 'context' dictionary contains data for the template (e.g., the OTP code)
        html_content = render_to_string('send_code.html', {'otp': otp_code, 'user': user})

        # 4. Construct and send the HTML email
        try:
            msg = EmailMessage(
                subject='Reset Your Password - Your New Code',  # Email Subject
                body=html_content,  # Use the rendered HTML content
                from_email='mdmamun340921@gmail.com', # Use settings.DEFAULT_FROM_EMAIL or a hardcoded email
                to=[email],  # Recipient list
            )
            msg.content_subtype = "html"  # Set the email type to HTML
            msg.send()

            return Response({'Message': 'OTP Has Been Resent To Your Email'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle potential email sending errors
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
class LoginAPIView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # ইউজারকে authenticate করো
            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    return Response({'error': 'Account not activated. Verify OTP first!'},
                                    status=status.HTTP_403_FORBIDDEN)

                login(request, user)

                # এবার User instance দিয়েই serializer তৈরি করবো
                user_serializer = UserLoginSerializer(user)
                return Response(user_serializer.data, status=status.HTTP_200_OK)

            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)


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

    # Ensure user is authenticated
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user  # Get the authenticated user from the token
            password = serializer.validated_data['password']

            # Update password
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
        return get_object_or_404(Profile, user=self.request.user)


""" -------------------Profile Update view----------------------- """

class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Profile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full profile data after update
        profile_serializer = ProfileSerializer(instance)
        return Response(profile_serializer.data)