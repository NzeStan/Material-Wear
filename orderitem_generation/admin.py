# orderitem_generation/admin.py
from django.contrib import messages
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.contenttypes.models import ContentType
from products.constants import STATES, CHURCH_CHOICES
from .api_views import (
    NyscKitPDFView, 
    NyscTourPDFView, 
    ChurchPDFView
)
import logging

logger = logging.getLogger(__name__)


class OrderItemGenerationAdminMixin:
    """
    Mixin to add PDF generation actions to Order admins
    
    Usage:
        Add this mixin to existing Order admin classes in order/admin.py
        
        Example:
            class NyscKitOrderAdmin(OrderItemGenerationAdminMixin, admin.ModelAdmin):
                ...
    """
    change_list_template = 'orderitem_generation/admin_changelist.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'generate-pdf/', 
                self.admin_site.admin_view(self.generate_pdf_view), 
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_generate_pdf'
            ),
        ]
        return custom_urls + urls
    
    def generate_pdf_view(self, request):
        """
        View to handle PDF generation with filter selection
        """
        if request.method == 'POST':
            filter_value = request.POST.get('filter_value')
            pdf_type = request.POST.get('pdf_type')
            
            if not filter_value:
                messages.error(request, 'Please select a filter value.')
                return self._redirect_to_changelist(request)
            
            # Call appropriate PDF view based on type
            try:
                if pdf_type == 'nysc_kit':
                    view = NyscKitPDFView.as_view()
                    request.GET = request.GET.copy()
                    request.GET['state'] = filter_value
                    
                elif pdf_type == 'nysc_tour':
                    view = NyscTourPDFView.as_view()
                    request.GET = request.GET.copy()
                    request.GET['state'] = filter_value
                    
                elif pdf_type == 'church':
                    view = ChurchPDFView.as_view()
                    request.GET = request.GET.copy()
                    request.GET['church'] = filter_value
                    
                else:
                    messages.error(request, 'Invalid PDF type.')
                    return self._redirect_to_changelist(request)
                
                # Generate and return PDF
                response = view(request)
                
                # Check if it's a successful PDF response
                if isinstance(response, HttpResponse) and response.status_code == 200:
                    return response
                else:
                    messages.error(request, 'No orders found for the selected filter.')
                    return self._redirect_to_changelist(request)
                    
            except Exception as e:
                logger.error(f"Error generating PDF: {str(e)}")
                messages.error(request, f'Error generating PDF: {str(e)}')
                return self._redirect_to_changelist(request)
        
        # GET request - show filter selection form
        context = self.get_pdf_context(request)
        return TemplateResponse(
            request,
            'orderitem_generation/generate_pdf_form.html',
            context
        )
    
    def _redirect_to_changelist(self, request):
        """Helper to redirect back to changelist"""
        from django.shortcuts import redirect
        changelist_url = f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist'
        return redirect(changelist_url)
    
    def get_pdf_context(self, request):
        """
        Override this method in subclasses to provide specific context
        Must return dict with: title, pdf_type, filter_label, filter_choices
        """
        raise NotImplementedError("Subclasses must implement get_pdf_context()")


# ============================================================================
# HELPER FUNCTIONS FOR ORDER/ADMIN.PY
# ============================================================================

def get_nysc_kit_pdf_context(admin_instance, request):
    """
    Get context for NYSC Kit PDF generation form
    Use this in NyscKitOrderAdmin.get_pdf_context()
    """
    from order.models import NyscKitOrder
    
    # Get states that have orders
    states_with_orders = NyscKitOrder.objects.filter(
        paid=True
    ).values_list('state', flat=True).distinct().order_by('state')
    
    return {
        'title': 'Generate NYSC Kit Orders PDF',
        'pdf_type': 'nysc_kit',
        'filter_label': 'Select State',
        'filter_choices': [(state, state) for state in states_with_orders],
        'opts': admin_instance.model._meta,
    }


def get_nysc_tour_pdf_context(admin_instance, request):
    """
    Get context for NYSC Tour PDF generation form
    Use this in NyscTourOrderAdmin.get_pdf_context()
    
    NOTE: NyscTourOrder has NO state field - we get states through products
    """
    from order.models import OrderItem
    from products.models import NyscTour
    
    # ✅ FIXED: Get states through product names (NyscTour.name = state)
    tour_type = ContentType.objects.get_for_model(NyscTour)
    
    # Get tour product IDs that have paid orders
    tour_product_ids = OrderItem.objects.filter(
        order__paid=True,
        content_type=tour_type
    ).values_list('object_id', flat=True).distinct()
    
    # Get state names from these products
    states_with_orders = NyscTour.objects.filter(
        id__in=tour_product_ids
    ).values_list('name', flat=True).distinct().order_by('name')
    
    return {
        'title': 'Generate NYSC Tour Orders PDF',
        'pdf_type': 'nysc_tour',
        'filter_label': 'Select State',
        'filter_choices': [(state, state) for state in states_with_orders],
        'opts': admin_instance.model._meta,
    }


def get_church_pdf_context(admin_instance, request):
    """
    Get context for Church PDF generation form
    Use this in ChurchOrderAdmin.get_pdf_context()
    """
    from order.models import OrderItem
    from products.models import Church
    
    # Get churches that have orders
    church_type = ContentType.objects.get_for_model(Church)
    churches_with_orders = OrderItem.objects.filter(
        order__paid=True,
        content_type=church_type
    ).values_list('product__church', flat=True).distinct().order_by('product__church')
    
    # Get church display names
    church_dict = dict(CHURCH_CHOICES)
    filter_choices = [(church, church_dict.get(church, church)) for church in churches_with_orders]
    
    return {
        'title': 'Generate Church Orders PDF',
        'pdf_type': 'church',
        'filter_label': 'Select Church',
        'filter_choices': filter_choices,
        'opts': admin_instance.model._meta,
    }