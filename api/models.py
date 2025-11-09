from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

# 🔹 Categoria merceologica
class Category(models.Model):
    name = models.CharField(max_length=100)
    tag = models.CharField(max_length=100, unique=True, null=True, blank=True)
    translations = models.JSONField(null=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# 🔹 Estensione profilo utente
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_currency = models.CharField(max_length=10, default='EUR')
    preferred_language = models.CharField(max_length=10, default='it')
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Profilo di {self.user.username}"

# 🔹 Prodotto
class Product(models.Model):
    translations = models.JSONField(null=True, blank=True)  # 🔹 Testi multilingua strutturati
    ean = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=20, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=10, null=True, blank=True, default='NA')
    categories = models.ManyToManyField(Category, blank=True)
    imported_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name="imported_products"
    )
    image_url = models.URLField(null=True, blank=True)

    ecoscore_grade = models.CharField(max_length=10, null=True, blank=True)
    nova_group = models.PositiveSmallIntegerField(null=True, blank=True)
    nutrition_grade = models.CharField(max_length=10, null=True, blank=True)
    packaging_tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    labels_tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    allergens_tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    additives_tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    origins_tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)

    ingredients_text = models.TextField(null=True, blank=True)
    ingredients = models.JSONField(null=True, blank=True)  # 🔹 Strutturati
    nutrients = models.JSONField(null=True, blank=True)    # 🔹 Valori nutrizionali

    raw_data = models.JSONField(null=True, blank=True)
    translations = models.JSONField(null=True, blank=True)  # 🔹 Testi multilingua strutturati

    last_synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.ean})"

# 🔹 Store (fisico o online)
class Store(models.Model):
    STORE_TYPE_CHOICES = [
        ('physical', 'Fisico'),
        ('online', 'Online'),
    ]
    name = models.CharField(max_length=255)
    store_type = models.CharField(max_length=10, choices=STORE_TYPE_CHOICES, default='physical')
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    url = models.URLField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

# 🔹 Prezzo
class Price(models.Model):
    PRICE_TYPE_CHOICES = [
        ('full', 'Prezzo pieno'),
        ('discount', 'Offerta'),
        ('card', 'Carta fedeltà'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='EUR')
    price_type = models.CharField(max_length=10, choices=PRICE_TYPE_CHOICES, default='full')
    date_inserted = models.DateField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.price} {self.currency} @ {self.store} - {self.product}"

# 🔹 Modifica proposta a un prodotto
class ProductChangeRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='change_requests')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    proposed_name = models.CharField(max_length=255, blank=True, null=True)
    proposed_brand = models.CharField(max_length=100, blank=True, null=True)
    proposed_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proposed_unit = models.CharField(max_length=20, blank=True, null=True)
    proposed_categories = models.ManyToManyField(Category, blank=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Modifica per {self.product.name} da {self.user}"

class ProductViewLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.product} at {self.timestamp}"

