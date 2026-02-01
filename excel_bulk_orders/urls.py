# excel_bulk_orders/urls.py
"""
URL Configuration for Excel Bulk Orders API.

Routes:
- /api/excel-bulk-orders/ - List/Create bulk orders
- /api/excel-bulk-orders/{id}/ - Retrieve/Update bulk order
- /api/excel-bulk-orders/{id}/upload/ - Upload Excel file
- /api/excel-bulk-orders/{id}/validate/ - Validate Excel
- /api/excel-bulk-orders/{id}/initialize-payment/ - Start payment
- /api/excel-bulk-orders/{id}/verify-payment/ - Verify payment
- /api/excel-bulk-orders/{id}/download-template/ - Download template
- /api/excel-participants/ - List participants
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExcelBulkOrderViewSet, ExcelParticipantViewSet

app_name = 'excel_bulk_orders'

router = DefaultRouter()
router.register(r'excel-bulk-orders', ExcelBulkOrderViewSet, basename='excelbulkorder')
router.register(r'excel-participants', ExcelParticipantViewSet, basename='excelparticipant')

urlpatterns = [
    path('', include(router.urls)),
]