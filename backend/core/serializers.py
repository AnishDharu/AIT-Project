from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import (
    Business, Category, Product, Customer, Supplier, Expense, Purchase,
    PurchaseItem, CustomerSale, SaleItem, StockMovement
)

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=160)

    def validate_username(self, value):
        from django.contrib.auth import get_user_model
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        Business.objects.create(name=validated_data["business_name"], owner=user)
        return user

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Product
        fields = ["id", "sku", "name", "category", "category_name", "description", "purchase_price",
                  "selling_price", "stock_quantity", "minimum_stock", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_category(self, category):
        if category and category.business_id != self.context["request"].business.id:
            raise serializers.ValidationError("Invalid category for this business.")
        return category

    def validate_sku(self, value):
        qs = Product.objects.filter(business=self.context["request"].business, sku=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("SKU already exists in this business.")
        return value

    def validate_stock_quantity(self, value):
        if self.instance and value != self.instance.stock_quantity:
            raise serializers.ValidationError("Use the stock adjustment workflow to change stock.")
        return value

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "address", "created_at"]
        read_only_fields = ["id", "created_at"]

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone", "address", "created_at"]
        read_only_fields = ["id", "created_at"]

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "category", "description", "amount", "expense_date", "payment_method", "created_at"]
        read_only_fields = ["id", "created_at"]

class SaleItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))

class SaleCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    sale_date = serializers.DateField(required=False)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"), default=Decimal("0.00"))
    tax_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"), default=Decimal("0.00"))
    payment_status = serializers.ChoiceField(choices=CustomerSale.PAYMENT_CHOICES, default="PAID")
    items = SaleItemInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        request = self.context["request"]
        business = request.business
        subtotal = Decimal("0.00")
        seen = set()
        for item in attrs["items"]:
            if item["product_id"] in seen:
                raise serializers.ValidationError("Combine duplicate product lines into one item.")
            seen.add(item["product_id"])
            try:
                product = Product.objects.get(pk=item["product_id"], business=business, is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product {item['product_id']} is unavailable.")
            if product.stock_quantity < item["quantity"]:
                raise serializers.ValidationError(f"Insufficient stock for {product.name}.")
            if item["unit_price"] < 0:
                raise serializers.ValidationError("Unit price cannot be negative.")
            subtotal += item["unit_price"] * item["quantity"]
        if attrs["discount_amount"] > subtotal:
            raise serializers.ValidationError("Discount cannot exceed subtotal.")
        if attrs.get("customer_id"):
            if not Customer.objects.filter(pk=attrs["customer_id"], business=business).exists():
                raise serializers.ValidationError("Customer does not belong to this business.")
        attrs["_subtotal"] = subtotal
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        business = request.business
        items = validated_data.pop("items")
        subtotal = validated_data.pop("_subtotal")
        customer_id = validated_data.pop("customer_id", None)
        discount = validated_data.pop("discount_amount", Decimal("0.00"))
        tax = validated_data.pop("tax_amount", Decimal("0.00"))
        sale_date = validated_data.pop("sale_date", timezone.localdate())
        payment_status = validated_data.pop("payment_status", "PAID")
        # Lock product rows and re-check stock to protect against concurrent sales.
        product_ids = [item["product_id"] for item in items]
        products = {p.id: p for p in Product.objects.select_for_update().filter(business=business, id__in=product_ids)}
        total = subtotal - discount + tax
        if total < 0:
            raise serializers.ValidationError("Sale total cannot be negative.")
        import uuid
        invoice = f"BF-{timezone.localdate():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
        sale = CustomerSale.objects.create(
            business=business, invoice_number=invoice,
            customer_id=customer_id, sale_date=sale_date,
            subtotal=subtotal, discount_amount=discount, tax_amount=tax,
            total_amount=total, payment_status=payment_status, created_by=request.user,
        )
        cogs = Decimal("0.00")
        for item in items:
            product = products.get(item["product_id"])
            if not product or product.stock_quantity < item["quantity"]:
                raise serializers.ValidationError("Stock changed during checkout. Please retry.")
            line_total = item["unit_price"] * item["quantity"]
            SaleItem.objects.create(sale=sale, product=product, quantity=item["quantity"],
                                    unit_price=item["unit_price"], unit_cost=product.purchase_price,
                                    line_total=line_total)
            previous = product.stock_quantity
            product.stock_quantity -= item["quantity"]
            product.save(update_fields=["stock_quantity", "updated_at"])
            StockMovement.objects.create(
                business=business, product=product, movement_type="SALE",
                quantity_change=-item["quantity"], previous_quantity=previous,
                new_quantity=product.stock_quantity, reason=f"Sale {invoice}", created_by=request.user,
            )
            cogs += product.purchase_price * item["quantity"]
        sale.cost_of_goods_sold = cogs
        sale.save(update_fields=["cost_of_goods_sold"])
        return sale

class SaleItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "unit_cost", "line_total"]

class SaleReadSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True, default="Walk-in")
    items = SaleItemReadSerializer(many=True, read_only=True)
    class Meta:
        model = CustomerSale
        fields = ["id", "invoice_number", "customer", "customer_name", "sale_date", "subtotal",
                  "discount_amount", "tax_amount", "total_amount", "cost_of_goods_sold",
                  "payment_status", "items", "created_at"]

class PurchaseItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))

class PurchaseCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    purchase_date = serializers.DateField(required=False)
    reference = serializers.CharField(max_length=60, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = PurchaseItemInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        business = self.context["request"].business
        if not Supplier.objects.filter(pk=attrs["supplier_id"], business=business).exists():
            raise serializers.ValidationError("Supplier does not belong to this business.")
        for item in attrs["items"]:
            if not Product.objects.filter(pk=item["product_id"], business=business, is_active=True).exists():
                raise serializers.ValidationError(f"Product {item['product_id']} is unavailable.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        business = request.business
        items = validated_data.pop("items")
        supplier_id = validated_data.pop("supplier_id")
        purchase = Purchase.objects.create(
            business=business, supplier_id=supplier_id,
            purchase_date=validated_data.pop("purchase_date", timezone.localdate()),
            reference=validated_data.pop("reference", ""),
            notes=validated_data.pop("notes", ""), total_amount=Decimal("0.00"),
            status="RECEIVED",
        )
        total = Decimal("0.00")
        product_ids = [i["product_id"] for i in items]
        products = {p.id: p for p in Product.objects.select_for_update().filter(business=business, id__in=product_ids)}
        for item in items:
            product = products[item["product_id"]]
            line_total = item["unit_cost"] * item["quantity"]
            PurchaseItem.objects.create(purchase=purchase, product=product, quantity=item["quantity"],
                                        unit_cost=item["unit_cost"], line_total=line_total)
            previous = product.stock_quantity
            product.stock_quantity += item["quantity"]
            # The latest purchase cost becomes the current indicative purchase cost.
            product.purchase_price = item["unit_cost"]
            product.save(update_fields=["stock_quantity", "purchase_price", "updated_at"])
            StockMovement.objects.create(
                business=business, product=product, movement_type="PURCHASE",
                quantity_change=item["quantity"], previous_quantity=previous,
                new_quantity=product.stock_quantity, reason=f"Purchase #{purchase.pk}", created_by=request.user,
            )
            total += line_total
        purchase.total_amount = total
        purchase.save(update_fields=["total_amount", "updated_at"])
        return purchase
