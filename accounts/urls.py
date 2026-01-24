# accounts/urls.py
from django.urls import path, include
from dj_rest_auth.registration.views import RegisterView
from .views import (
    # Social Auth
    GoogleLogin, 
    GithubLogin,
    
    # Authentication
    CustomLoginView, 
    CustomLogoutView,
    
    # User Status (NEW)
    UserStatusView,
    UserStatusBasicView,
    
    # Password Management
    CustomPasswordResetView, 
    CustomPasswordResetConfirmView,
    CustomPasswordChangeView,
    
    # User Details
    CustomUserDetailsView,
)

app_name = 'accounts'

urlpatterns = [
    # ========================================================================
    # REGISTRATION & LOGIN
    # ========================================================================
    path('register/', RegisterView.as_view(), name='rest_register'),
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('logout/', CustomLogoutView.as_view(), name='rest_logout'),
    
    # ========================================================================
    # USER STATUS ENDPOINTS (NEW)
    # ========================================================================
    # Comprehensive status with roles, permissions, and access control
    path('status/', UserStatusView.as_view(), name='user_status'),
    
    # Lightweight status for high-frequency checks
    path('status/basic/', UserStatusBasicView.as_view(), name='user_status_basic'),
    
    # ========================================================================
    # PASSWORD MANAGEMENT
    # ========================================================================
    path('password/reset/', CustomPasswordResetView.as_view(), name='rest_password_reset'),
    path('password/reset/confirm/', CustomPasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
    path('password/change/', CustomPasswordChangeView.as_view(), name='rest_password_change'),
    
    # ========================================================================
    # USER DETAILS
    # ========================================================================
    path('user/', CustomUserDetailsView.as_view(), name='rest_user_details'),
    
    # ========================================================================
    # SOCIAL AUTHENTICATION
    # ========================================================================
    path('social/google/', GoogleLogin.as_view(), name='google_login'),
    path('social/github/', GithubLogin.as_view(), name='github_login'),
    
    # ========================================================================
    # EMAIL VERIFICATION (dj-rest-auth registration)
    # ========================================================================
    path('registration/', include('dj_rest_auth.registration.urls')),
]

# Include allauth URLs for email verification (if needed)
# Note: These are primarily for the admin interface
urlpatterns += [
    path('', include('allauth.urls')),
]