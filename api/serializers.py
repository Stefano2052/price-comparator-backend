# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Price, Store, Category,
    UserProfile, ProductChangeRequest, ProductViewLog
)

# 🔹 Categoria Serializer
class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        allow_null=True
    )
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'children', 'is_approved']

    def get_children(self, obj):
        children = obj.children.all()
        return CategorySerializer(children, many=True, context=self.context).data


# 🔹 Store Serializer
class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'


# 🔹 Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    translations = serializers.JSONField(required=False)

    class Meta:
        model = Product
        fields = '__all__'


# 🔹 Price Serializer
class PriceSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField()

    class Meta:
        model = Price
        fields = [
            'id',
            'unit_price',
            'price',
            'currency',
            'price_type',
            'date_inserted',
            'is_approved',
            'product',
            'store',
            'user',
        ]
        read_only_fields = ['user']

    def get_unit_price(self, obj):
        quantity = getattr(obj.product, 'quantity', None)
        if quantity and quantity > 0:
            return round(obj.price / quantity, 4)
        return None


# 🔹 Product Change Request Serializer
class ProductChangeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductChangeRequest
        fields = '__all__'
        read_only_fields = ['user']


# 🔹 User Profile Serializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['preferred_currency', 'preferred_language', 'location']


# 🔹 User Serializer
class UserSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'userprofile']


# 🔹 Serializer per cronologia dei contributi
class UnifiedContributionSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    product_name = serializers.CharField()
    ean = serializers.CharField(allow_null=True)
    price = serializers.FloatField(allow_null=True)
    store_name = serializers.CharField(allow_null=True)
    date_inserted = serializers.DateTimeField()


# 🔹 Product View Log Serializer
class ProductViewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductViewLog
        fields = ['id', 'user', 'product', 'device_info', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp']
