from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Business, Category, Product

class Command(BaseCommand):
    help = "Create demo categories and products for the first available user."

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.order_by("id").first()
        if not user:
            self.stdout.write(self.style.ERROR("Create a user first with createsuperuser or the registration endpoint."))
            return
        business, _ = Business.objects.get_or_create(owner=user, defaults={"name": "Demo Business"})
        categories = {}
        for name in ["Electronics", "Office Supplies", "Daily Essentials"]:
            categories[name], _ = Category.objects.get_or_create(business=business, name=name)
        rows = [
            ("DEMO-001", "Wireless Mouse", "Electronics", "450.00", "699.00", 24, 5),
            ("DEMO-002", "Notebook Pack", "Office Supplies", "80.00", "129.00", 60, 10),
            ("DEMO-003", "USB-C Cable", "Electronics", "120.00", "249.00", 7, 8),
            ("DEMO-004", "Water Bottle", "Daily Essentials", "150.00", "299.00", 18, 5),
        ]
        created = 0
        for sku, name, cat, cost, price, stock, minimum in rows:
            _, was_created = Product.objects.get_or_create(
                business=business, sku=sku,
                defaults={"name": name, "category": categories[cat],
                          "purchase_price": Decimal(cost), "selling_price": Decimal(price),
                          "stock_quantity": stock, "minimum_stock": minimum}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Demo seed complete. {created} product(s) created for {business.name}."))
