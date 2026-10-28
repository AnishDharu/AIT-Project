from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

class Business(models.Model):
    name = models.CharField(max_length=160)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_businesses")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BusinessOwnedModel(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(BusinessOwnedModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["business", "name"], name="unique_category_name_per_business")]

    def __str__(self):
        return self.name

class Product(BusinessOwnedModel):
    sku = models.CharField(max_length=60)
    name = models.CharField(max_length=160)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    stock_quantity = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["business", "sku"], name="unique_product_sku_per_business")]
        indexes = [models.Index(fields=["business", "name"]), models.Index(fields=["business", "stock_quantity"])]

    def __str__(self):
        return f"{self.sku} — {self.name}"

class Customer(BusinessOwnedModel):
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

class Supplier(BusinessOwnedModel):
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

class Purchase(BusinessOwnedModel):
    STATUS_CHOICES = [("DRAFT", "Draft"), ("RECEIVED", "Received"), ("CANCELLED", "Cancelled")]
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchases")
    reference = models.CharField(max_length=60, blank=True)
    purchase_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="RECEIVED")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-purchase_date", "-id"]

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

class CustomerSale(BusinessOwnedModel):
    PAYMENT_CHOICES = [("UNPAID", "Unpaid"), ("PARTIAL", "Partial"), ("PAID", "Paid")]
    invoice_number = models.CharField(max_length=40)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True, related_name="sales")
    sale_date = models.DateField()
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    cost_of_goods_sold = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="PAID")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-sale_date", "-id"]
        constraints = [models.UniqueConstraint(fields=["business", "invoice_number"], name="unique_invoice_per_business")]
        indexes = [models.Index(fields=["business", "sale_date"])]

class SaleItem(models.Model):
    sale = models.ForeignKey(CustomerSale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

class Expense(BusinessOwnedModel):
    CATEGORY_CHOICES = [
        ("RENT", "Rent"), ("SALARY", "Salary"), ("UTILITIES", "Utilities"),
        ("TRANSPORT", "Transport"), ("MARKETING", "Marketing"),
        ("MAINTENANCE", "Maintenance"), ("OTHER", "Other"),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="OTHER")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    expense_date = models.DateField()
    payment_method = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-expense_date", "-id"]
        indexes = [models.Index(fields=["business", "expense_date"])]

class StockMovement(models.Model):
    MOVEMENT_CHOICES = [("PURCHASE", "Purchase"), ("SALE", "Sale"), ("ADJUSTMENT", "Adjustment")]
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=12, choices=MOVEMENT_CHOICES)
    quantity_change = models.IntegerField()
    previous_quantity = models.PositiveIntegerField()
    new_quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["business", "created_at"])]

class Notification(BusinessOwnedModel):
    title = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
