from pathlib import Path
from environs import Env
from datetime import timedelta
import cloudinary
import cloudinary.uploader
import cloudinary.api

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# CORE
# ==============================================================================

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

SITE_ID = 1
ROOT_URLCONF = "material.urls"
WSGI_APPLICATION = "material.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FORMS_URLFIELD_ASSUME_HTTPS = True


# ==============================================================================
# HOSTS & ORIGINS
# ==============================================================================

if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".ngrok-free.app"]
    CSRF_TRUSTED_ORIGINS = ["https://*.ngrok-free.app"]
else:
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


# ==============================================================================
# SECURITY  (single consolidated block — no duplicates)
# ==============================================================================

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_HTTPONLY = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


# ==============================================================================
# BRAND & COMPANY CONFIGURATION
# ==============================================================================

PRIMARY_COLOR = "#064E3B"
BACKGROUND_COLOR = "#FFFBEB"
ACCENT_COLOR = "#F59E0B"
TEXT_COLOR = "#1F2937"

COMPANY_NAME = "MATERIAL WEAR"
COMPANY_SHORT_NAME = "MATERIAL"
COMPANY_EMAIL = "contact@materialwear.com"
COMPANY_PHONE = "+2348071000804"
COMPANY_ADDRESS = "16 Emejiaka Street, Ngwa Rd, Aba Abia State"
COMPANY_LOGO_URL = (
    "https://res.cloudinary.com/dhhaiy58r/image/upload/v1721420288/"
    "Black_White_Minimalist_Clothes_Store_Logo_e1o8ow.png"
)

CURRENCY_SYMBOL = "₦"
CURRENCY_CODE = "NGN"

WHATSAPP_NUMBER = env.str("WHATSAPP_NUMBER", default="2348071000804")

SITE_URL = "http://127.0.0.1:8000" if DEBUG else "https://materialwear.com"
FRONTEND_URL = "http://localhost:3000" if DEBUG else "https://materialwear.com"


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
    # Two-Factor Authentication (must be before admin)
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
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
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "material.middleware.AdminIPWhitelistMiddleware",
    "axes.middleware.AxesMiddleware",
    "cart.middleware.CartCleanupMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

if DEBUG:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]


# ==============================================================================
# TEMPLATES  (admin + email only — React handles the frontend)
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

if DEBUG:
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
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

CACHE_TTL_SHORT = 60 * 5    # 5 minutes
CACHE_TTL_MEDIUM = 60 * 15  # 15 minutes
CACHE_TTL_LONG = 60 * 60    # 1 hour


# ==============================================================================
# AUTHENTICATION & AUTHORIZATION
# ==============================================================================

AUTH_USER_MODEL = "accounts.CustomUser"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # must be first
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ==============================================================================
# SESSION
# ==============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False
CART_SESSION_ID = "cart"


# ==============================================================================
# REST FRAMEWORK
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
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
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer"
    )
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
# JWT
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

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "mandatory" if not DEBUG else "optional"


# ==============================================================================
# CORS
# ==============================================================================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://materialwear.com",
        "https://www.materialwear.com",
        "https://material-wear.onrender.com",
    ]

CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
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
STATICFILES_DIRS = [BASE_DIR / "static"]

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
# YOUTUBE
# ==============================================================================

YOUTUBE_API_KEY = env("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = env("YOUTUBE_CHANNEL_ID")


# ==============================================================================
# DRF SPECTACULAR (API DOCS)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "MATERIAL Wear API",
    "DESCRIPTION": "Production-ready API for managing NYSC products, church merchandise, and orders",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVERS": [
        {"url": "https://materialwear.com", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Development"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/",
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",
    "ENUM_NAME_OVERRIDES": {
        "StateEnum": "products.constants.STATES",
        "UniversityStateEnum": "academic_directory.constants.NIGERIAN_STATES",
        "ProductSizeEnum": "products.constants.VEST_SIZES",
        "ChurchDenominationEnum": "products.constants.CHURCH_CHOICES",
        "ProductTypeEnum": "products.constants.PRODUCT_TYPE_CHOICES",
        "NyscKitTypeEnum": "products.constants.NYSC_KIT_TYPE_CHOICES",
        "UniversityTypeEnum": "academic_directory.constants.UNIVERSITY_TYPES",
        "PaymentStatusEnum": "payment.models.PAYMENT_STATUS_CHOICES",
        "TestimonialStatusEnum": "testimonials.constants.TestimonialStatus",
    },
    "TAGS": [
        {"name": "Authentication", "description": "User authentication"},
        {"name": "Products", "description": "Product catalog"},
        {"name": "Cart", "description": "Cart operations"},
        {"name": "Order", "description": "Order management"},
        {"name": "Payment", "description": "Payment processing"},
        {"name": "Measurement", "description": "Body measurements management"},
        {"name": "Bulk Orders", "description": "Bulk order management"},
        {"name": "Feed", "description": "Images and videos feed"},
        {"name": "Dropdowns", "description": "Dropdown data (states, LGAs, sizes)"},
    ],
}


# ==============================================================================
# ADMIN SECURITY — IP WHITELIST
# ==============================================================================

ADMIN_URL_PATH = "i_must_win/"
ADMIN_IP_WHITELIST = env.list(
    "ADMIN_IP_WHITELIST",
    default=[],  # Populate via environment variable in production
)


# ==============================================================================
# DJANGO-AXES (Brute-Force Protection)
# ==============================================================================

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_HANDLER = "axes.handlers.database.AxesDatabaseHandler"
AXES_VERBOSE = True
AXES_LOCKOUT_TEMPLATE = None
AXES_RESET_ON_SUCCESS = True
AXES_IPWARE_PROXY_COUNT = 1
AXES_IPWARE_META_PRECEDENCE_ORDER = [
    "HTTP_X_FORWARDED_FOR",
    "X_FORWARDED_FOR",
    "REMOTE_ADDR",
]
AXES_NEVER_LOCKOUT_WHITELIST = DEBUG  # Disable lockouts in development only


# ==============================================================================
# TWO-FACTOR AUTHENTICATION
# ==============================================================================

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "/i_must_win/"
TWO_FACTOR_PATCH_ADMIN = not DEBUG  # Enforce 2FA on admin in production only
TWO_FACTOR_QR_FACTORY = "qrcode.image.pil.PilImage"
TWO_FACTOR_TOTP_DIGITS = 6
TWO_FACTOR_REMEMBER_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
TWO_FACTOR_CALL_GATEWAY = None   # No phone/SMS — authenticator app only
TWO_FACTOR_SMS_GATEWAY = None
TWO_FACTOR_SETUP_SUCCESS_URL = "/i_must_win/"


# ==============================================================================
# TESTIMONIALS
# ==============================================================================

TESTIMONIALS_USE_CACHE = True
TESTIMONIALS_USE_UUIDS = True
TESTIMONIALS_ENABLE_DASHBOARD = True
TESTIMONIALS_SEND_EMAIL_NOTIFICATIONS = True
TESTIMONIALS_SEND_ADMIN_NOTIFICATIONS = True
TESTIMONIALS_USE_BACKGROUND_TASKS = True
TESTIMONIALS_NOTIFICATION_EMAIL = env(
    "TESTIMONIALS_NOTIFICATION_EMAIL", default="nnamaniifeanyi10@gmail.com"
)


# ==============================================================================
# BACKGROUND TASKS
# ==============================================================================

MAX_ATTEMPTS = 3
BACKGROUND_TASK_RUN_ASYNC = True


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True


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