# accounts/views.py
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView, 
    PasswordResetView, PasswordResetConfirmView, UserDetailsView
)
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings
import logging

from .serializers import (
    LogoutSerializer, 
    UserStatusSerializer,
    CustomUserSerializer,
    ChangePasswordSerializer
)

logger = logging.getLogger(__name__)


# ============================================================================
# USER STATUS ENDPOINT
# ============================================================================

class UserStatusView(APIView):
    """
    Check if the current user is authenticated and return basic user info.
    This is useful for frontend to determine auth state without fetching full user details.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Check authentication status",
        description="""
        Returns the authentication status of the current request.
        
        - If authenticated: returns user basic info
        - If not authenticated: returns is_authenticated=false
        
        This endpoint is useful for:
        - Checking if user is logged in
        - Getting basic user info without full details
        - Frontend auth state management
        """,
        responses={
            200: UserStatusSerializer,
        },
        examples=[
            {
                'name': 'Authenticated Response',
                'value': {
                    'is_authenticated': True,
                    'user': {
                        'id': '123e4567-e89b-12d3-a456-426614174000',
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'full_name': 'John Doe'
                    }
                }
            },
            {
                'name': 'Unauthenticated Response',
                'value': {
                    'is_authenticated': False,
                    'user': None
                }
            }
        ]
    )
    def get(self, request):
        """Get authentication status"""
        if request.user.is_authenticated:
            data = {
                'is_authenticated': True,
                'user': request.user
            }
            serializer = UserStatusSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response({
            'is_authenticated': False,
            'user': None
        }, status=status.HTTP_200_OK)


# ============================================================================
# SOCIAL AUTHENTICATION
# ============================================================================

class GoogleLogin(SocialLoginView):
    """
    Login/Register with Google OAuth2
    """
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    throttle_classes = [AnonRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Google OAuth Login",
        description="""
        Authenticate using Google OAuth2 token.
        
        Process:
        1. Frontend obtains Google OAuth token
        2. Send token to this endpoint
        3. Backend validates token with Google
        4. Creates user if new, or logs in existing user
        5. Returns authentication tokens
        
        If an account with the same email exists, it will be linked to the Google account.
        """,
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Authentication failed"),
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                logger.info(f"Google OAuth login successful")
            return response
        except Exception as e:
            logger.error(f"Google OAuth login failed: {str(e)}")
            return Response(
                {"detail": "Google authentication failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )


class GithubLogin(SocialLoginView):
    """
    Login/Register with GitHub OAuth2
    """
    adapter_class = GitHubOAuth2Adapter
    client_class = OAuth2Client
    throttle_classes = [AnonRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="GitHub OAuth Login",
        description="""
        Authenticate using GitHub OAuth2 token.
        
        Process:
        1. Frontend obtains GitHub OAuth token
        2. Send token to this endpoint
        3. Backend validates token with GitHub
        4. Creates user if new, or logs in existing user
        5. Returns authentication tokens
        
        If an account with the same email exists, it will be linked to the GitHub account.
        """,
        responses={
            200: OpenApiResponse(description="Login successful"),
            400: OpenApiResponse(description="Authentication failed"),
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                logger.info(f"GitHub OAuth login successful")
            return response
        except Exception as e:
            logger.error(f"GitHub OAuth login failed: {str(e)}")
            return Response(
                {"detail": "GitHub authentication failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================================
# AUTHENTICATION VIEWS
# ============================================================================

class CustomLoginView(LoginView):
    """
    Custom login view with logging
    """
    throttle_classes = [AnonRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Login with email and password",
        description="Authenticate user with email and password credentials"
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"User logged in successfully: {request.data.get('email')}")
        return response


class CustomLogoutView(LogoutView):
    """
    Logout the current user and clear session
    """
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Logout current user",
        description="""
        Logout the authenticated user.
        
        This will:
        - Invalidate the current session
        - Clear authentication cookies
        - Logout the user from the system
        """,
        responses={
            200: OpenApiResponse(
                description="Successfully logged out",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': 'Successfully logged out.'}
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        logger.info(f"User logged out: {request.user.email}")
        return super().post(request, *args, **kwargs)


# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

class CustomPasswordResetView(PasswordResetView):
    """
    Request password reset email
    """
    throttle_classes = [AnonRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Request password reset",
        description="""
        Request a password reset email.
        
        An email will be sent to the provided address with a link to reset the password.
        The link is valid for a limited time.
        """,
        responses={
            200: OpenApiResponse(description="Password reset email sent"),
            400: OpenApiResponse(description="Invalid email or validation error"),
        }
    )
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        logger.info(f"Password reset requested for: {email}")
        return super().post(request, *args, **kwargs)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Confirm password reset with new password
    """
    throttle_classes = [AnonRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Confirm password reset",
        description="""
        Reset password using the token from the reset email.
        
        Required fields:
        - uid: User ID from email link
        - token: Reset token from email link
        - new_password1: New password
        - new_password2: Confirm new password
        """,
        responses={
            200: OpenApiResponse(description="Password reset successful"),
            400: OpenApiResponse(description="Invalid token or passwords don't match"),
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomPasswordChangeView(PasswordChangeView):
    """
    Change password for authenticated user
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Change password",
        description="""
        Change password for the currently authenticated user.
        
        Required fields:
        - old_password: Current password
        - new_password1: New password
        - new_password2: Confirm new password
        
        The new password must meet Django's password validation requirements.
        """,
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                response={
                    'type': 'object',
                    'properties': {
                        'detail': {'type': 'string', 'example': 'Password changed successfully'}
                    }
                }
            ),
            400: OpenApiResponse(description="Invalid password or validation error"),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Password changed for user: {request.user.email}")
        return Response(
            {"detail": "Password changed successfully"},
            status=status.HTTP_200_OK
        )


# ============================================================================
# USER DETAILS
# ============================================================================

class CustomUserDetailsView(UserDetailsView):
    """
    Get or update user profile details
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer
    throttle_classes = [UserRateThrottle]
    
    @extend_schema(
        tags=['Authentication'],
        summary="Get user details",
        description="Retrieve the authenticated user's profile information",
        responses={
            200: CustomUserSerializer,
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Authentication'],
        summary="Update user details",
        description="""
        Update the authenticated user's profile information.
        
        Updatable fields:
        - first_name
        - last_name
        
        Read-only fields:
        - id, email, is_active, date_joined, last_login
        """,
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def put(self, request, *args, **kwargs):
        """Full update of user details"""
        return self.partial_update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['Authentication'],
        summary="Partially update user details",
        description="Partially update the authenticated user's profile information",
        responses={
            200: CustomUserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def patch(self, request, *args, **kwargs):
        """Partial update of user details"""
        return self.partial_update(request, *args, **kwargs)