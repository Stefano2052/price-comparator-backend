from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    ProductViewLogViewSet, ProductViewSet, PriceViewSet, StoreViewSet,
    CategoryViewSet, ProductChangeRequestViewSet, UserPreferencesView,
    UserContributionsView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views_firebase import FirebaseAuthConvertView, CurrentUserMe   

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'prices', PriceViewSet, basename='price')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'product-changes', ProductChangeRequestViewSet, basename='productchangerequest')
router.register(r'product-view-log', ProductViewLogViewSet, basename='productviewlog')

urlpatterns = [
    path('', include(router.urls)),
    path('user/preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    path('user/contributions/', UserContributionsView.as_view(), name='user-contributions'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('search/', views.search_products, name='search_products'),
    path('recent-product-views/', views.recent_product_views, name='recent_product_views'),
    path('convert-token/', FirebaseAuthConvertView.as_view(), name='convert_token'),
    path('users/me/', CurrentUserMe.as_view(), name='users-me'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
