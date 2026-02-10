"""URL Configuration for Academic Directory API"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PublicSubmissionView,
    RepresentativeViewSet,
    UniversityViewSet,
    FacultyViewSet,
    DepartmentViewSet,
    PDFGenerationView,
    DashboardView,
    NotificationViewSet
)

app_name = 'academic_directory'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'representatives', RepresentativeViewSet, basename='representative')
router.register(r'universities', UniversityViewSet, basename='university')
router.register(r'faculties', FacultyViewSet, basename='faculty')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Public endpoint (no auth required)
    path('submit/', PublicSubmissionView.as_view(), name='public-submit'),
    
    # Admin endpoints (auth required)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('export-pdf/', PDFGenerationView.as_view(), name='export-pdf'),
    
    # Include router URLs
    path('', include(router.urls)),
]