from django.contrib import admin
from .models import Business, Category, Product, Customer, Supplier, Purchase, PurchaseItem, CustomerSale, SaleItem, Expense, StockMovement, Notification

admin.site.register(Business)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Customer)
admin.site.register(Supplier)
admin.site.register(Purchase)
admin.site.register(PurchaseItem)
admin.site.register(CustomerSale)
admin.site.register(SaleItem)
admin.site.register(Expense)
admin.site.register(StockMovement)
admin.site.register(Notification)
