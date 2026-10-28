from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Business, Category, Product
from decimal import Decimal

class BizFlowModelTests(TestCase):
    def test_business_product_setup(self):
        user = get_user_model().objects.create_user(username="owner-test", password="Test-password-123")
        business = Business.objects.create(name="Test Business", owner=user)
        category = Category.objects.create(business=business, name="General")
        product = Product.objects.create(
            business=business, category=category, sku="TEST-1", name="Test item",
            purchase_price=Decimal("10.00"), selling_price=Decimal("15.00"),
            stock_quantity=5, minimum_stock=2
        )
        self.assertEqual(product.business_id, business.id)
        self.assertEqual(product.stock_quantity, 5)
