# products/api_views.py
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from .models import Category, NyscKit, NyscTour, Church
from .serializers import (
    CategorySerializer, NyscKitSerializer, NyscTourSerializer, 
    ChurchSerializer, ProductListSerializer
)
from .constants import (
    STATES, LGAS, VEST_SIZES, CHURCH_SIZES, CHURCH_CHOICES,
    get_lgas_for_state, get_all_states_list
)


class ProductPagination(PageNumberPagination):
    """Custom pagination for products"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(description="List all categories with product counts"),
    retrieve=extend_schema(description="Get specific category details"),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for product categories - Read only"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 15))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(description="List all NYSC Kit products with filters"),
    retrieve=extend_schema(description="Get specific NYSC Kit product details"),
)
class NyscKitViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for NYSC Kit products"""
    serializer_class = NyscKitSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'type', 'available', 'out_of_stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created', 'name']
    ordering = ['type', 'name']  # Default ordering
    lookup_field = 'id'
    
    def get_queryset(self):
        """Optimized queryset with select_related"""
        return NyscKit.objects.select_related('category').filter(available=True)
    
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(description="List all NYSC Tour products with filters"),
    retrieve=extend_schema(description="Get specific NYSC Tour product details"),
)
class NyscTourViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for NYSC Tour products"""
    serializer_class = NyscTourSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'available', 'out_of_stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created', 'name']
    ordering = ['name']  # Default ordering
    lookup_field = 'id'
    
    def get_queryset(self):
        """Optimized queryset with select_related"""
        return NyscTour.objects.select_related('category').filter(available=True)
    
    @method_decorator(cache_page(60 * 10))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 30))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(description="List all Church merchandise products with filters"),
    retrieve=extend_schema(description="Get specific Church product details"),
)
class ChurchViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for Church merchandise products"""
    serializer_class = ChurchSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'church', 'available', 'out_of_stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created', 'name']
    ordering = ['church', 'name']  # Default ordering
    lookup_field = 'id'
    
    def get_queryset(self):
        """Optimized queryset with select_related"""
        return Church.objects.select_related('category').filter(available=True)
    
    @method_decorator(cache_page(60 * 10))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 30))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    description="Get all products grouped by type with optional category filtering",
    responses={200: ProductListSerializer}, 
    parameters=[
        OpenApiParameter(
            name='category',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Filter by category slug',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Limit items per product type (default: 4)',
            required=False
        ),
    ]
)
class ProductListView(views.APIView):
    """
    Combined product list endpoint - returns all product types grouped
    Optimized for storefront display
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer 
    @method_decorator(cache_page(60 * 10))
    @method_decorator(vary_on_cookie)
    def get(self, request):
        category_slug = request.query_params.get('category')
        limit = int(request.query_params.get('limit', 4))
        
        # Get all categories
        categories = Category.objects.all()
        current_category = None
        
        # Base querysets with optimization
        nysc_kits = NyscKit.objects.select_related('category').filter(available=True)
        nysc_tours = NyscTour.objects.select_related('category').filter(available=True)
        churches = Church.objects.select_related('category').filter(available=True)
        
        # Apply category filter if provided
        if category_slug:
            try:
                current_category = Category.objects.get(slug=category_slug)
                nysc_kits = nysc_kits.filter(category=current_category)
                nysc_tours = nysc_tours.filter(category=current_category)
                churches = churches.filter(category=current_category)
            except Category.DoesNotExist:
                pass
        
        # Get counts for pagination info
        total_kits = nysc_kits.count()
        total_tours = nysc_tours.count()
        total_churches = churches.count()
        
        # Apply limit for initial load
        nysc_kits = nysc_kits[:limit]
        nysc_tours = nysc_tours[:limit]
        churches = churches[:limit]
        
        # Serialize data
        data = {
            'nysc_kits': NyscKitSerializer(nysc_kits, many=True, context={'request': request}).data,
            'nysc_tours': NyscTourSerializer(nysc_tours, many=True, context={'request': request}).data,
            'churches': ChurchSerializer(churches, many=True, context={'request': request}).data,
            'categories': CategorySerializer(categories, many=True).data,
            'current_category': CategorySerializer(current_category).data if current_category else None,
            'pagination': {
                'nysc_kits': {
                    'showing': len(nysc_kits),
                    'total': total_kits,
                    'has_more': total_kits > limit
                },
                'nysc_tours': {
                    'showing': len(nysc_tours),
                    'total': total_tours,
                    'has_more': total_tours > limit
                },
                'churches': {
                    'showing': len(churches),
                    'total': total_churches,
                    'has_more': total_churches > limit
                },
            }
        }
        
        return Response(data)

@extend_schema(tags=['Dropdowns'])
class StatesListView(views.APIView):
    """
    Get list of all Nigerian states
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Get list of all Nigerian states",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'states': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'display': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """Return all states"""
        states_data = [
            {'value': value, 'display': display}
            for value, display in STATES if value  # Exclude empty option
        ]
        return Response({
            'states': states_data
        })


@extend_schema(tags=['Dropdowns'])
class LGAsListView(views.APIView):
    """
    Get list of LGAs for a specific state
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Get list of Local Government Areas for a specific state",
        parameters=[
            OpenApiParameter(
                name='state',
                type=str,
                location=OpenApiParameter.QUERY,
                description='State name to get LGAs for',
                required=True
            ),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'state': {'type': 'string'},
                    'lgas': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'display': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'State parameter is required'},
            404: {'description': 'Invalid state name'}
        }
    )
    def get(self, request):
        """Return LGAs for specified state with validation"""
        state = request.query_params.get('state')
        
        if not state:
            return Response({
                'error': 'State parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate that state exists
        valid_states = [s[0] for s in STATES if s[0]]  # Get all state codes/names
        if state not in valid_states:
            return Response({
                'error': f'Invalid state: {state}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        lgas = get_lgas_for_state(state)
        lgas_data = [
            {'value': value, 'display': display}
            for value, display in lgas if value  # Exclude empty option
        ]
        
        return Response({
            'state': state,
            'lgas': lgas_data
        })





@extend_schema(tags=['Dropdowns'])
class SizesListView(views.APIView):
    """
    Get list of available sizes for products
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Get list of available sizes (for Vest and Church products)",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'vest_sizes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'display': {'type': 'string'}
                            }
                        }
                    },
                    'church_sizes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'display': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """Return available sizes"""
        vest_sizes_data = [
            {'value': value, 'display': display}
            for value, display in VEST_SIZES if value  # Exclude empty option
        ]
        
        church_sizes_data = [
            {'value': value, 'display': display}
            for value, display in CHURCH_SIZES if value  # Exclude empty option
        ]
        
        return Response({
            'vest_sizes': vest_sizes_data,
            'church_sizes': church_sizes_data,
            'note': 'Vest and Church products use the same size options'
        })


@extend_schema(tags=['Dropdowns'])
class ChurchesListView(views.APIView):
    """
    Get list of available churches
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Get list of available churches",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'churches': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'display': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """Return available churches"""
        churches_data = [
            {'value': value, 'display': display}
            for value, display in CHURCH_CHOICES if value  # Exclude empty option
        ]
        
        return Response({
            'churches': churches_data
        })


@extend_schema(tags=['Dropdowns'])
class AllDropdownsView(views.APIView):
    """
    Get all dropdown data in one request
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Get all dropdown data (states, sizes, churches) in a single request",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'states': {'type': 'array'},
                    'sizes': {'type': 'object'},
                    'churches': {'type': 'array'},
                    'note': {'type': 'string'}
                }
            }
        }
    )
    def get(self, request):
        """Return all dropdown data"""
        states_data = [
            {'value': value, 'display': display}
            for value, display in STATES if value
        ]
        
        sizes_data = {
            'vest_sizes': [
                {'value': value, 'display': display}
                for value, display in VEST_SIZES if value
            ],
            'church_sizes': [
                {'value': value, 'display': display}
                for value, display in CHURCH_SIZES if value
            ]
        }
        
        churches_data = [
            {'value': value, 'display': display}
            for value, display in CHURCH_CHOICES if value
        ]
        
        return Response({
            'states': states_data,
            'sizes': sizes_data,
            'churches': churches_data,
            'note': 'For LGAs, use the /api/products/lgas/?state=<state_name> endpoint'
        })
