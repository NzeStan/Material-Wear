# material/settings.py
"""
Django settings for MATERIAL project - Production-Ready API Architecture

Brand Colors:
- Primary: #064E3B (Dark Green)
- Background: #FFFBEB (Cream)
- Accent: #F59E0B (Gold)
- Text: #1F2937 (Dark Gray)
"""

from pathlib import Path
from environs import Env
import os
from datetime import timedelta
import cloudinary
import cloudinary.uploader
import cloudinary.api

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# SECURITY
# ==============================================================================

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

if not DEBUG:
    ALLOWED_HOSTS = [
        "material-wear.onrender.com",
        "www.materialwear.com",
        "materialwear.com",
    ]
    CSRF_TRUSTED_ORIGINS = [
        "https://material-wear.onrender.com",
        "https://www.materialwear.com",
        "https://materialwear.com",
    ]
    # Security settings for production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    ALLOWED_HOSTS = [
        "localhost",
        "127.0.0.1",
        ".ngrok-free.app",
    ]
    CSRF_TRUSTED_ORIGINS = ["https://*.ngrok-free.app"]

# ==============================================================================
# BRAND CONFIGURATION
# ==============================================================================

# Brand Colors
PRIMARY_COLOR = "#064E3B"  # Dark Green
BACKGROUND_COLOR = "#FFFBEB"  # Cream
ACCENT_COLOR = "#F59E0B"  # Gold
TEXT_COLOR = "#1F2937"  # Dark Gray

# Company Information
COMPANY_NAME = "MATERIAL WEAR"
COMPANY_SHORT_NAME = "MATERIAL"
COMPANY_EMAIL = "contact@materialwear.com"
COMPANY_PHONE = "+2348071000804"
COMPANY_ADDRESS = "16 Emejiaka Street, Ngwa Rd, Aba Abia State"
COMPANY_LOGO_URL = "https://res.cloudinary.com/dhhaiy58r/image/upload/v1721420288/Black_White_Minimalist_Clothes_Store_Logo_e1o8ow.png"

# Currency
CURRENCY_SYMBOL = "₦"
CURRENCY_CODE = "NGN"

# ==============================================================================
# APPLICATIONS
# ==============================================================================

INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Two-Factor Authentication (must be before admin usage)
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    "two_factor.plugins.phonenumber",  # Optional: for SMS backup
    # Brute-force protection
    "axes",
    # REST Framework & Auth
    "rest_framework",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "rest_framework_simplejwt",
    # Social Authentication
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    # Third-party utilities
    "django_filters",
    "drf_spectacular",
    "whitenoise.runserver_nostatic",
    "background_task",
    "corsheaders",
    "testimonials",
    # Local apps
    "accounts.apps.AccountsConfig",
    "products.apps.ProductsConfig",
    "cart.apps.CartConfig",
    "measurement.apps.MeasurementConfig",
    "feed.apps.FeedConfig",
    "order.apps.OrderConfig",
    "payment.apps.PaymentConfig",
    "bulk_orders.apps.BulkOrdersConfig",
    "webhook_router.apps.WebhookRouterConfig",
    "orderitem_generation.apps.OrderitemGenerationConfig",
    "referrals.apps.ReferralsConfig",
    "excel_bulk_orders.apps.ExcelBulkOrdersConfig",
    "academic_directory.apps.AcademicDirectoryConfig",
    "image_bulk_orders.apps.ImageBulkOrdersConfig",
    "live_forms.apps.LiveFormsConfig",
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # OTP verification middleware (required for two-factor auth)
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Admin IP whitelist (blocks non-whitelisted IPs in production)
    "material.middleware.AdminIPWhitelistMiddleware",
    # Brute-force protection (must be after AuthenticationMiddleware)
    "axes.middleware.AxesMiddleware",
    "cart.middleware.CartCleanupMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

if DEBUG:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# ==============================================================================
# TEMPLATES (Minimal - for admin and email only)
# ==============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# DATABASE
# ==============================================================================

DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", default="postgresql://localhost/material")
}

# ==============================================================================
# CACHING
# ==============================================================================
# Production, dummy cache for development
if DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache_table",
            "KEY_PREFIX": "material",
            "TIMEOUT": 300,
        }
    }


# Cache time settings (in seconds)
CACHE_TTL_SHORT = 60 * 5  # 5 minutes
CACHE_TTL_MEDIUM = 60 * 15  # 15 minutes
CACHE_TTL_LONG = 60 * 60  # 1 hour

# ==============================================================================
# AUTHENTICATION & AUTHORIZATION
# ==============================================================================

AUTH_USER_MODEL = "accounts.CustomUser"

AUTHENTICATION_BACKENDS = [
    # Axes backend must be first for brute-force protection
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "django_otp.backends.OtpBackend",
]

# ==============================================================================
# SESSION & COOKIE SECURITY
# ==============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
CART_SESSION_ID = "cart"

# ✅ PRODUCTION SECURITY SETTINGS
if not DEBUG:
    # Secure cookies in production
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # SameSite cookie settings
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

    # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
else:
    # Development settings
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # ✅ ADD THROTTLING CONFIGURATION
    "DEFAULT_THROTTLE_CLASSES": [
        "material.throttling.BurstUserRateThrottle",
        "material.throttling.SustainedUserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "checkout": "10/hour",
        "payment": "10/hour",
        "cart": "100/hour",
        "anon_strict": "50/hour",
        "burst": "20/minute",
        "sustained": "500/hour",
        "live_form_submit": "30/hour",
        "live_form_view": "200/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # ✅ SECURITY SETTINGS
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # Only allow browsable API in debug mode
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

# Add browsable API only in DEBUG mode
if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer"
    )

# Add authentication based on environment
if DEBUG:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ]
else:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ]

# ==============================================================================
# JWT CONFIGURATION
# ==============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1 if DEBUG else 15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7 if DEBUG else 1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ==============================================================================
# DRF SPECTACULAR (API DOCUMENTATION)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    # Basic Info
    "TITLE": "MATERIAL Wear API",
    "DESCRIPTION": "Production-ready API for managing NYSC products, church merchandise, and orders",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Server Configuration
    "SERVERS": [
        {"url": "https://materialwear.com", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Development"},
    ],
    # Schema Generation
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",
    "ENUM_NAME_OVERRIDES": {
        # State choices
        "StateEnum": "products.constants.STATES",
        # Size choices - unified since VEST_SIZES and CHURCH_SIZES are identical
        "ProductSizeEnum": "products.constants.VEST_SIZES",
        # Church choices
        "ChurchDenominationEnum": "products.constants.CHURCH_CHOICES",
        # Product type choices
        "ProductTypeEnum": "products.constants.PRODUCT_TYPE_CHOICES",
        # NYSC Kit type choices
        "NyscKitTypeEnum": "products.constants.NYSC_KIT_TYPE_CHOICES",
    },
    # ✅ ADD THIS to suppress unnecessary blank/null enums
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    # ✅ ADD THIS to generate name from label
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
    # ✅ AUTHENTICATION CONFIGURATION
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "sessionid",
                "description": "Session-based authentication using Django session cookie",
            },
            "tokenAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Token-based authentication (if using tokens)",
            },
        }
    },
    "SECURITY": [
        {"cookieAuth": []},  # Default to cookie auth
    ],
    # ✅ SWAGGER UI CONFIGURATION
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
    },
    # Additional Settings
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    "ENUM_ADD_EXPLICIT_BLANK_NULL_CHOICE": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    # API Tags
    "TAGS": [
        {
            "name": "Authentication",
            "description": "User authentication and account management",
        },
        {"name": "Products", "description": "Product catalog and details"},
        {"name": "Cart", "description": "Shopping cart operations"},
        {"name": "Order", "description": "Order management"},
        {"name": "Payment", "description": "Payment processing"},
        {"name": "Measurement", "description": "Body measurements management"},
        {"name": "Bulk Orders", "description": "Bulk order management"},
        {"name": "Feed", "description": "Images and videos feed"},
        {"name": "Dropdowns", "description": "Dropdown data (states, LGAs, sizes)"},
    ],
}

# ==============================================================================
# REST AUTH
# ==============================================================================

REST_AUTH = {
    "USE_JWT": not DEBUG,
    "JWT_AUTH_HTTPONLY": False,
    "JWT_AUTH_COOKIE": "material-auth",
    "JWT_AUTH_REFRESH_COOKIE": "material-refresh",
}

# ==============================================================================
# DJANGO ALLAUTH
# ==============================================================================

SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory" if not DEBUG else "optional"

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================

# ✅ SECURE CORS CONFIGURATION
if DEBUG:
    # Development - allow localhost
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
else:
    # Production - ONLY allow your actual domains
    CORS_ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        # Add your actual production domains here
    ]

# ✅ CRITICAL: NEVER set this to True in production
CORS_ALLOW_ALL_ORIGINS = False

# Allow credentials (cookies, sessions)
CORS_ALLOW_CREDENTIALS = True

# Allowed HTTP methods
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Allowed headers
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]


# ==============================================================================
# STATIC & MEDIA FILES
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# ==============================================================================
# CLOUDINARY
# ==============================================================================

cloudinary.config(
    cloud_name=env("CLOUDINARY_CLOUD_NAME"),
    api_key=env("CLOUDINARY_API_KEY"),
    api_secret=env("CLOUDINARY_API_SECRET"),
    secure=True,
)

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

# ==============================================================================
# EMAIL
# ==============================================================================

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@materialwear.com")

# ==============================================================================
# PAYMENT (PAYSTACK)
# ==============================================================================

PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY")
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY")
PAYSTACK_WEBHOOK_SECRET = env("PAYSTACK_WEBHOOK_SECRET", default="")

# ==============================================================================
# YOUITUBE KEYS
# ==============================================================================
YOUTUBE_API_KEY = env("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = env("YOUTUBE_CHANNEL_ID")

# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# OTHER SETTINGS
# ==============================================================================

ROOT_URLCONF = "material.urls"
WSGI_APPLICATION = "material.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Debug toolbar
if DEBUG:
    INTERNAL_IPS = ["127.0.0.1"]

# Background tasks
MAX_ATTEMPTS = 3
BACKGROUND_TASK_RUN_ASYNC = True

# ==============================================================================
# Frontend URL
# ==============================================================================
FRONTEND_URL = "https://materialwear.com" if not DEBUG else "http://localhost:3000"

# ==============================================================================
# WhatsApp Number
# ==============================================================================
WHATSAPP_NUMBER = env.str(
    "WHATSAPP_NUMBER", default="2348071000804"
)  # MATERIAL Contact Number


# Set SITE_URL based on environment
if DEBUG:
    SITE_URL = "http://127.0.0.1:8000"
else:
    SITE_URL = "https://yourdomain.com"


# testimonials
TESTIMONIALS_USE_CACHE = True
TESTIMONIALS_NOTIFICATION_EMAIL = "admin@yoursite.com"
TESTIMONIALS_USE_UUIDS = True
TESTIMONIALS_ENABLE_DASHBOARD = True
TESTIMONIALS_NOTIFICATION_EMAIL = "nnamaniifeanyi10@gmail.com"
TESTIMONIALS_SEND_EMAIL_NOTIFICATIONS = True
TESTIMONIALS_SEND_ADMIN_NOTIFICATIONS = True
TESTIMONIALS_USE_BACKGROUND_TASKS = True

# ==============================================================================
# ADMIN SECURITY - IP WHITELIST
# ==============================================================================
# Only these IPs can access /i_must_win/ (admin) in production
# Add your trusted IPs here (e.g., office IP, your home IP, etc.)
ADMIN_URL_PATH = "i_must_win/"
ADMIN_IP_WHITELIST = env.list(
    "ADMIN_IP_WHITELIST",
    default=[
        # Add your whitelisted IPs here or via environment variable
        # Example: '102.88.34.56', '41.184.123.45'
    ],
)

# ==============================================================================
# DJANGO-AXES CONFIGURATION (Brute-Force Protection)
# ==============================================================================
# Lockout after N failed login attempts
AXES_FAILURE_LIMIT = 5

# Lockout duration in hours (1 hour = 3600 seconds)
AXES_COOLOFF_TIME = 1  # 1 hour

# Lock based on IP + username combination (more secure)
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]

# Use database backend for storing access attempts
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"

# Enable verbose logging of access attempts
AXES_VERBOSE = True

# Custom lockout response
AXES_LOCKOUT_TEMPLATE = None  # Uses default, or set to 'axes/lockout.html'

# Reset failed attempts on successful login
AXES_RESET_ON_SUCCESS = True

# IP header for proxy deployments (Render, Heroku, etc.)
AXES_IPWARE_PROXY_COUNT = 1
AXES_IPWARE_META_PRECEDENCE_ORDER = [
    "HTTP_X_FORWARDED_FOR",
    "X_FORWARDED_FOR",
    "REMOTE_ADDR",
]

# Whitelist certain IPs from being locked out (e.g., health checks)
AXES_NEVER_LOCKOUT_WHITELIST = DEBUG  # Only in development

# ==============================================================================
# TWO-FACTOR AUTHENTICATION CONFIGURATION
# ==============================================================================
# Login URL for two-factor auth
LOGIN_URL = "two_factor:login"

# Redirect after successful 2FA login
LOGIN_REDIRECT_URL = "/i_must_win/"

# Only use TOTP (authenticator apps) - no phone/SMS
TWO_FACTOR_PATCH_ADMIN = True  # Patch the admin to require 2FA

# QR code generation settings
TWO_FACTOR_QR_FACTORY = "qrcode.image.pil.PilImage"

# Issuer name shown in authenticator apps
TWO_FACTOR_TOTP_DIGITS = 6

# Number of backup tokens to generate
TWO_FACTOR_REMEMBER_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days

# Disable phone verification (authenticator app only)
TWO_FACTOR_CALL_GATEWAY = None
TWO_FACTOR_SMS_GATEWAY = None

TWO_FACTOR_SETUP_SUCCESS_URL = "/i_must_win/"
