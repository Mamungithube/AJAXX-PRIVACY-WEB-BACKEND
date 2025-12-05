from django.urls import path
from .views import (
    IsAdminCheckView, 
    UserAPIView, 
    RegisterAPIView, 
    LoginAPIView, 
    LogoutAPIView, 
    VerifyOTPApiView,
    ResendOTPApiView,
    ForgotPasswordAPIView ,
    ProfileDetailView, 
    ProfileUpdateView, 
    AdminDeleteUserView,
    TotalUserCountView,
    ChangePasswordViewSet,
    UserBlockViewSet,
    GoogleLoginAPIView
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    # user list and show
    path('user_all/', UserAPIView.as_view(), name='user-list'),  
    path("accounts/user_all/<int:pk>/", UserAPIView.as_view()),
    

    #user register and login and logout and active
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('auth/google/', GoogleLoginAPIView.as_view(), name='google-login'),
    path('resend_otp/', ResendOTPApiView.as_view(), name='resend-otp'),
    path('verify_otp/', VerifyOTPApiView.as_view(), name='verify-otp'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('admin/delete-user/<int:user_id>/', AdminDeleteUserView.as_view(), name='admin-delete-user'),
    path('users/count/', TotalUserCountView.as_view(), name='user-count'),
    path('user/is-admin/', IsAdminCheckView.as_view(), name='is-admin'),
    path('change_pass/',ChangePasswordViewSet.as_view({'post':'create'}), name='change_password'),
    path('BlockUser/<int:pk>/', UserBlockViewSet.as_view({'post':'block'}), name='block-user'),
    path('BlockUser/<int:pk>/unblock/', UserBlockViewSet.as_view({'post':'unblock'}), name='unblock-user'),

    
    # profile detail and update
    path('profile/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
]