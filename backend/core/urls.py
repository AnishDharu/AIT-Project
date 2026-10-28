from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, MeView, CategoryViewSet, ProductViewSet, CustomerViewSet,
    SupplierViewSet, ExpenseViewSet, SalesView, SaleDetailView, PurchasesView,
    DashboardSummaryView, DashboardSalesChartView, api_root, BusinessHealthView, DeadStockView,
    PurchasePlannerView, CopilotView, ReportsView, StockAdjustmentView, InvoicePDFView, PurchaseOCRView
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("customers", CustomerViewSet, basename="customer")
router.register("suppliers", SupplierViewSet, basename="supplier")
router.register("expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", api_root),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("sales/", SalesView.as_view(), name="sales"),
    path("sales/<int:pk>/", SaleDetailView.as_view(), name="sale-detail"),
    path("purchases/", PurchasesView.as_view(), name="purchases"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/sales-chart/", DashboardSalesChartView.as_view(), name="dashboard-sales-chart"),
    path("dashboard/health/", BusinessHealthView.as_view(), name="dashboard-health"),
    path("dead-stock/", DeadStockView.as_view(), name="dead-stock"),
    path("purchase-planner/", PurchasePlannerView.as_view(), name="purchase-planner"),
    path("copilot/", CopilotView.as_view(), name="business-copilot"),
    path("reports/", ReportsView.as_view(), name="reports"),
    path("products/<int:pk>/stock-adjustment/", StockAdjustmentView.as_view(), name="stock-adjustment"),
    path("sales/<int:pk>/invoice.pdf", InvoicePDFView.as_view(), name="invoice-pdf"),
    path("purchase-ocr/", PurchaseOCRView.as_view(), name="purchase-ocr"),
    path("", include(router.urls)),
]
