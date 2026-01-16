# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    CategoryViewSet, NyscKitViewSet, NyscTourViewSet, 
    ChurchViewSet, ProductListView, StatesListView, LGAsListView, SizesListView, 
    ChurchesListView, AllDropdownsView
)



app_name = "products"

# Create API router
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'nysc-kits', NyscKitViewSet, basename='nysc-kit')
router.register(r'nysc-tours', NyscTourViewSet, basename='nysc-tour')
router.register(r'churches', ChurchViewSet, basename='church')

urlpatterns = [
    # Combined product list endpoint
    path('all/', ProductListView.as_view(), name='product-list'),
    # Dropdown endpoints
    path('dropdowns/states/', StatesListView.as_view(), name='states-list'),
    path('dropdowns/lgas/', LGAsListView.as_view(), name='lgas-list'),
    path('dropdowns/sizes/', SizesListView.as_view(), name='sizes-list'),
    path('dropdowns/churches/', ChurchesListView.as_view(), name='churches-list'),
    path('dropdowns/all/', AllDropdownsView.as_view(), name='all-dropdowns'),
    # Router URLs
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# GET    /api/products/all/                          # Get all products grouped by type
# GET    /api/products/all/?category=<slug>          # Filter by category
# GET    /api/products/all/?limit=<int>              # Limit items per type
#
# CATEGORIES:
# GET    /api/products/categories/                   # List all categories
# GET    /api/products/categories/<slug>/            # Get specific category
#
# NYSC KITS:
# GET    /api/products/nysc-kits/                    # List all NYSC kits
# GET    /api/products/nysc-kits/<id>/               # Get specific NYSC kit
# GET    /api/products/nysc-kits/?type=<type>        # Filter by type (kakhi, vest, cap)
# GET    /api/products/nysc-kits/?category=<id>      # Filter by category
# GET    /api/products/nysc-kits/?search=<query>     # Search by name/description
# GET    /api/products/nysc-kits/?ordering=price     # Order by price, created, name
#
# NYSC TOURS:
# GET    /api/products/nysc-tours/                   # List all NYSC tours
# GET    /api/products/nysc-tours/<id>/              # Get specific NYSC tour
# GET    /api/products/nysc-tours/?category=<id>     # Filter by category
# GET    /api/products/nysc-tours/?search=<query>    # Search by name/description
# GET    /api/products/nysc-tours/?ordering=price    # Order by price, created, name
#
# CHURCHES:
# GET    /api/products/churches/                     # List all church products
# GET    /api/products/churches/<id>/                # Get specific church product
# GET    /api/products/churches/?church=<church>     # Filter by church
# GET    /api/products/churches/?category=<id>       # Filter by category
# GET    /api/products/churches/?search=<query>      # Search by name/description
# GET    /api/products/churches/?ordering=price      # Order by price, created, name

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# GET    /api/products/dropdowns/states/                 # Get all states
# GET    /api/products/dropdowns/lgas/?state=<state>     # Get LGAs for a state
# GET    /api/products/dropdowns/sizes/                  # Get all sizes
# GET    /api/products/dropdowns/churches/               # Get all churches
# GET    /api/products/dropdowns/all/                    # Get all dropdowns
#
# ============================================================================
# USAGE EXAMPLES
# ============================================================================
# Get all states:
# GET /api/products/dropdowns/states/
#
# Get LGAs for Lagos:
# GET /api/products/dropdowns/lgas/?state=Lagos
#
# Get all sizes:
# GET /api/products/dropdowns/sizes/
#
# Get all churches:
# GET /api/products/dropdowns/churches/
#
# Get everything in one request:
# GET /api/products/dropdowns/all/
