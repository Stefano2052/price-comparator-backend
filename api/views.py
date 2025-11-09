# views.py

from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import (
    Product, Price, Store, Category,
    ProductChangeRequest, UserProfile, ProductViewLog
)
from .serializers import (
    ProductSerializer, PriceSerializer, StoreSerializer,
    CategorySerializer, ProductChangeRequestSerializer,
    UserProfileSerializer, UnifiedContributionSerializer, ProductViewLogSerializer
)

# 🔹 Helper comune per applicare filtri in base ai permessi
def _get_queryset_by_permission(user, queryset, public_filter=None):
    if user.is_authenticated and user.is_staff:
        return queryset
    return queryset.filter(**(public_filter or {}))


# 🔹 ViewSets principali

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'ean', 'brand', 'is_approved']

    def get_queryset(self):
        qs = Product.objects.select_related('user').prefetch_related('categories')
        return _get_queryset_by_permission(self.request.user, qs, {'is_approved': True})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

        # 🔹 Endpoint custom per suggerimento brand
    @action(detail=False, methods=['get'], url_path='brands', permission_classes=[permissions.AllowAny])
    def brands(self, request):
        """
        Restituisce l'elenco dei brand unici, con filtro opzionale via ?search=
        """
        query = request.query_params.get('search', '').strip().lower()
        brands = Product.objects.exclude(brand__isnull=True).exclude(brand__exact='')

        if query:
            brands = brands.filter(brand__icontains=query)

        unique_brands = (
            brands.values_list('brand', flat=True)
            .distinct()
            .order_by('brand')
        )

        return Response(list(unique_brands))



class PriceViewSet(viewsets.ModelViewSet):
    serializer_class = PriceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'date_inserted', 'store', 'price_type']

    def get_queryset(self):
        qs = Price.objects.select_related('product', 'store', 'user')
        return _get_queryset_by_permission(self.request.user, qs, {'is_approved': True})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['store_type', 'verified']

    def get_queryset(self):
        qs = Store.objects.all()
        return _get_queryset_by_permission(self.request.user, qs, {'verified': True})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'tag', 'parent', 'is_approved']

    def get_queryset(self):
        qs = Category.objects.all()
        qs = _get_queryset_by_permission(self.request.user, qs, {'is_approved': True})
        if 'parent' not in self.request.query_params:
            return qs.filter(parent=None)
        return qs


class ProductChangeRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ProductChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'is_approved', 'is_rejected']

    def get_queryset(self):
        qs = ProductChangeRequest.objects.select_related('product', 'user')
        return qs if self.request.user.is_staff else qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductViewLogViewSet(viewsets.ModelViewSet):
    serializer_class = ProductViewLogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return ProductViewLog.objects.select_related('product', 'user')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)


# 🔹 APIView - Preferenze utente

class UserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


# 🔹 APIView - Contributi utente

class UserContributionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        price_data = Price.objects.filter(user=user).select_related('product', 'store')
        product_data = Product.objects.filter(user=user)
        mod_data = ProductChangeRequest.objects.filter(user=user).select_related('product')

        contributions = []

        for p in price_data:
            contributions.append({
                'id': str(p.id),
                'type': 'price',
                'status': 'approved' if p.is_approved else 'pending',
                'product_name': p.product.name,
                'ean': p.product.ean,
                'price': float(p.price),
                'store_name': p.store.name,
                'date_inserted': p.date_inserted,
            })

        for p in product_data:
            contributions.append({
                'id': str(p.id),
                'type': 'product',
                'status': 'approved' if p.is_approved else 'pending',
                'product_name': p.name,
                'ean': p.ean,
                'price': None,
                'store_name': None,
                'date_inserted': p.created_at,
            })

        for m in mod_data:
            contributions.append({
                'id': str(m.id),
                'type': 'modification',
                'status': 'approved' if m.is_approved else ('rejected' if m.is_rejected else 'pending'),
                'product_name': m.product.name,
                'ean': m.product.ean,
                'price': None,
                'store_name': None,
                'date_inserted': m.created_at,
            })

        contributions.sort(key=lambda x: x['date_inserted'], reverse=True)

        serializer = UnifiedContributionSerializer(contributions, many=True)
        return Response(serializer.data)


# 🔹 Funzione API - Ricerca prodotti

@api_view(['GET'])
def search_products(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(ean__icontains=query)
        )[:5]  # massimo 5 risultati
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    return Response([])


# 🔹 Funzione API - Recupero prodotti visti recentemente

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_product_views(request):
    user = request.user

    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 10))

    logs = ProductViewLog.objects.filter(user=user).select_related('product').order_by('-timestamp')[offset:offset+limit]

    results = [
        {
            'id': log.product.id,
            'name': log.product.name,
            'ean': log.product.ean,
            'image_url': log.product.image_url,
            'viewed_at': log.timestamp,
        }
        for log in logs
    ]

    return Response(results)

