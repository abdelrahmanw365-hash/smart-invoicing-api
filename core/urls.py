from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from inventory.views import (
    ProductViewSet,
    ClientViewSet,
    ExpenseViewSet,
    InvoiceViewSet,
    DashboardAPIView,
    generate_pdf
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔥 The Security Login & Token Refresh endpoints!
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('api/invoices/<int:pk>/pdf/', generate_pdf, name='generate_pdf'),
    path('api/', include(router.urls)),
]