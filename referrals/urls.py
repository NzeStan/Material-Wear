from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReferrerProfileViewSet, PromotionalMediaViewSet, SharePayloadViewSet


app_name = 'referrals'

router = DefaultRouter()
router.register(r'profiles', ReferrerProfileViewSet, basename='referrer-profile')
router.register(r'media', PromotionalMediaViewSet, basename='promotional-media')
router.register(r'share', SharePayloadViewSet, basename='share-payload')

urlpatterns = [
    path('', include(router.urls)),
]