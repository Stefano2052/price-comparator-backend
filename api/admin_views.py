# admin_views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import Product, Price, Store, Category, ProductChangeRequest


@staff_member_required
def unapproved_items(request):
    """Display all unapproved entries for admin review."""
    context = {
        "products": Product.objects.filter(is_approved=False),
        "prices": Price.objects.filter(is_approved=False),
        "stores": Store.objects.filter(verified=False),
        "categories": Category.objects.filter(is_approved=False),
        "changes": ProductChangeRequest.objects.filter(is_approved=False, is_rejected=False),
    }
    return render(request, "admin/unapproved_items.html", context)
