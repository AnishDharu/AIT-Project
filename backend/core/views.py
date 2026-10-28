from decimal import Decimal
import json
import os
import urllib.error
import urllib.request
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Business, Category, Product, Customer, Supplier, Expense, Purchase, CustomerSale, SaleItem, StockMovement
from .serializers import (
    RegisterSerializer, UserSerializer, CategorySerializer, ProductSerializer, CustomerSerializer,
    SupplierSerializer, ExpenseSerializer, SaleCreateSerializer, SaleReadSerializer, PurchaseCreateSerializer
)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"message": "Account created. Log in to continue.", "user": UserSerializer(user).data},
                        status=status.HTTP_201_CREATED)

class BusinessContextMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated:
            business = Business.objects.filter(owner=request.user).order_by("id").first()
            if business is None:
                raise PermissionDenied("No business is associated with this account.")
            request.business = business

class BusinessModelViewSet(BusinessContextMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return self.queryset.filter(business=self.request.business)
    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class CategoryViewSet(BusinessModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(BusinessModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(sku__icontains=search)
        low_stock = self.request.query_params.get("low_stock")
        if low_stock == "true":
            qs = qs.filter(stock_quantity__lte=F("minimum_stock"))
        return qs

class CustomerViewSet(BusinessModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SupplierViewSet(BusinessModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class ExpenseViewSet(BusinessModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

class SalesView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        sales = CustomerSale.objects.filter(business=request.business).select_related("customer").prefetch_related("items__product")
        return Response(SaleReadSerializer(sales, many=True).data)
    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        sale = CustomerSale.objects.select_related("customer").prefetch_related("items__product").get(pk=sale.pk)
        return Response(SaleReadSerializer(sale).data, status=status.HTTP_201_CREATED)

class SaleDetailView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, pk):
        try:
            sale = CustomerSale.objects.select_related("customer").prefetch_related("items__product").get(pk=pk, business=request.business)
        except CustomerSale.DoesNotExist:
            return Response({"detail": "Sale not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SaleReadSerializer(sale).data)

class PurchasesView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        purchases = Purchase.objects.filter(business=request.business).select_related("supplier").prefetch_related("items__product")
        return Response([{
            "id": p.id, "supplier": p.supplier.name, "reference": p.reference,
            "purchase_date": p.purchase_date, "total_amount": p.total_amount,
            "status": p.status, "items_count": p.items.count()
        } for p in purchases])
    def post(self, request):
        serializer = PurchaseCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        purchase = serializer.save()
        return Response({"id": purchase.id, "total_amount": purchase.total_amount, "status": purchase.status},
                        status=status.HTTP_201_CREATED)

class DashboardSummaryView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        business = request.business
        today = timezone.localdate()
        sales = CustomerSale.objects.filter(business=business, sale_date__year=today.year, sale_date__month=today.month)
        expenses = Expense.objects.filter(business=business, expense_date__year=today.year, expense_date__month=today.month)
        revenue = sales.aggregate(v=Sum("total_amount"))["v"] or Decimal("0.00")
        cogs = sales.aggregate(v=Sum("cost_of_goods_sold"))["v"] or Decimal("0.00")
        expense_total = expenses.aggregate(v=Sum("amount"))["v"] or Decimal("0.00")
        product_qs = Product.objects.filter(business=business, is_active=True)
        return Response({
            "business_name": business.name,
            "period": today.strftime("%B %Y"),
            "monthly_revenue": revenue,
            "monthly_cogs": cogs,
            "monthly_expenses": expense_total,
            "estimated_net_profit": revenue - cogs - expense_total,
            "total_products": product_qs.count(),
            "low_stock_products": product_qs.filter(stock_quantity__lte=F("minimum_stock")).count(),
            "total_customers": Customer.objects.filter(business=business).count(),
            "total_suppliers": Supplier.objects.filter(business=business).count(),
            "sales_count": sales.count(),
        })

class DashboardSalesChartView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        rows = (CustomerSale.objects.filter(business=request.business)
                .annotate(month=TruncMonth("sale_date"))
                .values("month").annotate(revenue=Sum("total_amount"), transactions=Count("id"))
                .order_by("month")[:12])
        return Response([{"month": r["month"].strftime("%b %Y"), "revenue": r["revenue"], "transactions": r["transactions"]} for r in rows])

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def api_root(request):
    return Response({
        "name": "BizFlow API",
        "version": "0.1.0",
        "endpoints": ["auth/register/", "auth/token/", "auth/me/", "categories/", "products/",
                      "customers/", "suppliers/", "expenses/", "sales/", "purchases/",
                      "dashboard/summary/", "dashboard/sales-chart/"]
    })

# Extended BizFlow capabilities: reports, rule-based copilot, purchase planning,
# dead-stock analysis, stock adjustments, invoice PDF, and optional OCR extraction.
from datetime import timedelta
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.utils.dateparse import parse_date

class BusinessHealthView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        b = request.business
        today = timezone.localdate()
        products = Product.objects.filter(business=b, is_active=True)
        total_products = products.count()
        low_stock = products.filter(stock_quantity__lte=F('minimum_stock')).count()
        inventory_score = round(((total_products-low_stock)/total_products)*100) if total_products else 0
        month_sales = CustomerSale.objects.filter(business=b, sale_date__year=today.year, sale_date__month=today.month)
        revenue = month_sales.aggregate(v=Sum('total_amount'))['v'] or Decimal('0')
        cogs = month_sales.aggregate(v=Sum('cost_of_goods_sold'))['v'] or Decimal('0')
        expenses = Expense.objects.filter(business=b, expense_date__year=today.year, expense_date__month=today.month).aggregate(v=Sum('amount'))['v'] or Decimal('0')
        net_profit = revenue - cogs - expenses
        sales_score = min(100, round(float(revenue)/100000*100))
        profit_margin = (net_profit / revenue * 100) if revenue else Decimal('0')
        profit_score = max(0, min(100, round(float(profit_margin))))
        health = round(inventory_score*.30 + sales_score*.35 + profit_score*.35)
        return Response({'business_name':b.name,'inventory_score':inventory_score,'sales_score':sales_score,'profit_margin_score':profit_score,'profit_margin':round(float(profit_margin),2),'business_health_score':health,'total_products':total_products,'low_stock_products':low_stock,'monthly_revenue':revenue,'monthly_net_profit':net_profit,'sales_target_assumption':100000,'note':'Scores are rule-based indicators. Sales score uses a configurable illustrative ₹1,00,000 monthly target.'})

class DeadStockView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        b=request.business; cutoff=timezone.localdate()-timedelta(days=15)
        products=Product.objects.filter(business=b,is_active=True).annotate(last_sale=Max('saleitem__sale__sale_date'))
        rows=[]
        for p in products:
            days=(timezone.localdate()-p.last_sale).days if p.last_sale else None
            dead=(days is None or days>=15)
            if dead:
                rows.append({'id':p.id,'sku':p.sku,'name':p.name,'stock_quantity':p.stock_quantity,'last_sale_date':p.last_sale,'days_since_sale':days,'status':'NO SALES RECORDED' if days is None else 'DEAD STOCK'})
        return Response({'threshold_days':15,'count':len(rows),'items':rows,'note':'Products with no recorded sales are listed separately because no sale date exists.'})

class PurchasePlannerView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        b=request.business; since=timezone.localdate()-timedelta(days=30); items=[]
        for p in Product.objects.filter(business=b,is_active=True).order_by('name'):
            sold=SaleItem.objects.filter(sale__business=b,sale__sale_date__gte=since,product=p).aggregate(q=Sum('quantity'))['q'] or 0
            daily=float(sold)/30; target=max(p.minimum_stock*2, round(daily*30))
            needed=max(0,target-p.stock_quantity)
            if needed or p.stock_quantity<=p.minimum_stock:
                items.append({'product_id':p.id,'sku':p.sku,'product_name':p.name,'current_stock':p.stock_quantity,'minimum_stock':p.minimum_stock,'units_sold_last_30_days':sold,'suggested_purchase_quantity':needed,'estimated_cost':str((p.purchase_price*needed).quantize(Decimal('0.01'))),'reason':'Below minimum stock' if p.stock_quantity<=p.minimum_stock else 'Replenishment based on 30-day sales'})
        return Response({'based_on':'Last 30 days of recorded sales and configured minimum stock','recommendations':items,'count':len(items),'note':'Heuristic planning support, not a machine-learning forecast.'})

class CopilotView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        b=request.business; prompt=str(request.data.get('message','')).strip()
        today=timezone.localdate(); month=CustomerSale.objects.filter(business=b,sale_date__year=today.year,sale_date__month=today.month)
        revenue=month.aggregate(v=Sum('total_amount'))['v'] or Decimal('0'); cogs=month.aggregate(v=Sum('cost_of_goods_sold'))['v'] or Decimal('0')
        expenses=Expense.objects.filter(business=b,expense_date__year=today.year,expense_date__month=today.month).aggregate(v=Sum('amount'))['v'] or Decimal('0')
        low=list(Product.objects.filter(business=b,is_active=True,stock_quantity__lte=F('minimum_stock')).values('name','stock_quantity','minimum_stock')[:8])
        dead_count=0
        for p in Product.objects.filter(business=b,is_active=True).annotate(last_sale=Max('saleitem__sale__sale_date')):
            if not p.last_sale or (today-p.last_sale).days>=15: dead_count+=1
        insights=[]
        if low: insights.append(f'{len(low)} product(s) are at or below minimum stock. Review replenishment before accepting more orders.')
        else: insights.append('No products are currently at or below their configured minimum stock.')
        insights.append(f'This month recorded revenue is ₹{revenue:,.2f}; estimated profit after recorded product cost and expenses is ₹{(revenue-cogs-expenses):,.2f}.')
        if dead_count: insights.append(f'{dead_count} product(s) meet the 15-day dead-stock rule or have no recorded sale. Verify product activity before discounting or reordering.')
        ai_answer = None
        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        ai_status = 'rule_based_fallback'
        if prompt and api_key and api_key != 'YOUR_NEW_GEMINI_API_KEY':
            try:
                context = {
                    'business': b.name, 'user_question': prompt[:1000],
                    'month_revenue_inr': str(revenue), 'month_cost_of_goods_sold_inr': str(cogs),
                    'month_expenses_inr': str(expenses), 'estimated_net_profit_inr': str(revenue-cogs-expenses),
                    'low_stock_products': low, 'dead_stock_count_15_day_rule': dead_count,
                    'instructions': 'Give practical, cautious small-business advice based only on supplied data. Clearly label assumptions; do not invent figures.'
                }
                payload = json.dumps({'contents':[{'parts':[{'text':json.dumps(context, ensure_ascii=False)}]}],
                                      'generationConfig':{'temperature':0.3,'maxOutputTokens':700}}).encode('utf-8')
                req = urllib.request.Request(
                    'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + api_key,
                    data=payload, headers={'Content-Type':'application/json'}, method='POST')
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                ai_answer = ''.join(part.get('text','') for part in result.get('candidates',[{}])[0].get('content',{}).get('parts',[])).strip()
                if ai_answer: ai_status = 'gemini_connected'
                else: ai_status = 'rule_based_fallback'
            except Exception:
                # Do not expose provider errors or secrets; retain useful local insights.
                ai_status = 'rule_based_fallback'
        if prompt and not ai_answer:
            insights.insert(0, f'Request considered: “{prompt[:240]}”. The response below is based on recorded business rules and database data.')
        return Response({'mode':'gemini_ai' if ai_answer else 'rule_based_business_copilot', 'answer':ai_answer,
                         'insights':insights,'low_stock_products':low,'monthly_revenue':revenue,
                         'estimated_net_profit':revenue-cogs-expenses,'dead_stock_count':dead_count,
                         'ai_integration_status':ai_status})

class ReportsView(BusinessContextMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        b=request.business; today=timezone.localdate(); kind=request.query_params.get('range','7d')
        start=parse_date(request.query_params.get('start','')) if request.query_params.get('start') else None
        end=parse_date(request.query_params.get('end','')) if request.query_params.get('end') else None
        if kind=='today': start=end=today
        elif kind=='7d': start=today-timedelta(days=6); end=today
        elif kind=='30d': start=today-timedelta(days=29); end=today
        elif kind=='6m': start=today-timedelta(days=182); end=today
        elif kind=='custom':
            if not start or not end or start>end: return Response({'detail':'For custom range, provide valid start and end dates (YYYY-MM-DD).'},status=400)
        else: return Response({'detail':'range must be today, 7d, 30d, 6m, or custom.'},status=400)
        sales=CustomerSale.objects.filter(business=b,sale_date__range=(start,end))
        agg=sales.aggregate(revenue=Sum('total_amount'),cogs=Sum('cost_of_goods_sold'),bills=Count('id'))
        revenue=agg['revenue'] or Decimal('0'); cogs=agg['cogs'] or Decimal('0'); bills=agg['bills'] or 0
        expense=Expense.objects.filter(business=b,expense_date__range=(start,end)).aggregate(v=Sum('amount'))['v'] or Decimal('0')
        return Response({'range':kind,'start_date':start,'end_date':end,'total_sales':revenue,'total_bills':bills,'average_bill_value':(revenue/bills if bills else Decimal('0')),'cost_of_goods_sold':cogs,'expenses':expense,'estimated_profit':revenue-cogs-expense,'transactions':SaleReadSerializer(sales.select_related('customer').prefetch_related('items__product'),many=True).data})

class StockAdjustmentView(BusinessContextMixin, APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self, request, pk):
        try: p=Product.objects.get(pk=pk,business=request.business,is_active=True)
        except Product.DoesNotExist: return Response({'detail':'Product not found.'},status=404)
        try: quantity=int(request.data.get('quantity_change'))
        except (TypeError,ValueError): return Response({'detail':'quantity_change must be an integer.'},status=400)
        if not quantity: return Response({'detail':'Quantity change cannot be zero.'},status=400)
        with transaction.atomic():
            p=Product.objects.select_for_update().get(pk=p.pk)
            new=p.stock_quantity+quantity
            if new<0: return Response({'detail':'Stock cannot become negative.'},status=400)
            old=p.stock_quantity;p.stock_quantity=new;p.save(update_fields=['stock_quantity','updated_at'])
            StockMovement.objects.create(business=request.business,product=p,movement_type='ADJUSTMENT',quantity_change=quantity,previous_quantity=old,new_quantity=new,reason=str(request.data.get('reason','Manual stock adjustment'))[:255],created_by=request.user)
        return Response({'product_id':p.id,'stock_quantity':p.stock_quantity})

class InvoicePDFView(BusinessContextMixin, APIView):
    permission_classes=[permissions.IsAuthenticated]
    def get(self, request, pk):
        try: sale=CustomerSale.objects.select_related('business','customer').prefetch_related('items__product').get(pk=pk,business=request.business)
        except CustomerSale.DoesNotExist: return Response({'detail':'Invoice not found.'},status=404)
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from io import BytesIO
        except ImportError: return Response({'detail':'Install reportlab with: python -m pip install reportlab'},status=501)
        buf=BytesIO(); c=canvas.Canvas(buf,pagesize=A4); width,height=A4; y=height-48
        c.setFont('Helvetica-Bold',18);c.drawString(48,y,sale.business.name);y-=28
        c.setFont('Helvetica-Bold',13);c.drawString(48,y,'TAX INVOICE');y-=22
        c.setFont('Helvetica',10);c.drawString(48,y,f'Invoice: {sale.invoice_number}');c.drawString(340,y,f'Date: {sale.sale_date}');y-=18
        c.drawString(48,y,f'Customer: {sale.customer.name if sale.customer else "Walk-in customer"}');y-=30
        c.setFont('Helvetica-Bold',10);c.drawString(48,y,'Product');c.drawString(310,y,'Qty');c.drawString(360,y,'Unit Price');c.drawString(460,y,'Amount');y-=16
        c.setFont('Helvetica',9)
        for item in sale.items.all():
            if y<90: c.showPage();y=height-50;c.setFont('Helvetica',9)
            c.drawString(48,y,item.product.name[:38]);c.drawRightString(335,y,str(item.quantity));c.drawRightString(425,y,f'{item.unit_price:.2f}');c.drawRightString(545,y,f'{item.line_total:.2f}');y-=16
        y-=12;c.drawRightString(545,y,f'Subtotal: INR {sale.subtotal:.2f}');y-=16;c.drawRightString(545,y,f'Discount: INR {sale.discount_amount:.2f}');y-=16;c.drawRightString(545,y,f'GST/Tax: INR {sale.tax_amount:.2f}');y-=20
        c.setFont('Helvetica-Bold',12);c.drawRightString(545,y,f'TOTAL: INR {sale.total_amount:.2f}');y-=28
        c.setFont('Helvetica',8);c.drawString(48,y,'Generated by BizFlow. Confirm business tax details before using as a statutory GST invoice.')
        c.save();response=HttpResponse(buf.getvalue(),content_type='application/pdf');response['Content-Disposition']=f'attachment; filename="{sale.invoice_number}.pdf"';return response

class PurchaseOCRView(BusinessContextMixin, APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self, request):
        upload=request.FILES.get('file')
        if not upload: return Response({'detail':'Upload an image or PDF invoice using the file field.'},status=400)
        if upload.size>10*1024*1024: return Response({'detail':'File exceeds 10 MB limit.'},status=400)
        if upload.content_type not in ['image/png','image/jpeg','image/webp','application/pdf']: return Response({'detail':'Supported formats: PNG, JPG, WEBP, PDF.'},status=400)
        try:
            if upload.content_type=='application/pdf':
                try:
                    import fitz
                    doc=fitz.open(stream=upload.read(),filetype='pdf'); text='\n'.join(page.get_text() for page in doc)
                    if not text.strip(): return Response({'detail':'PDF appears scanned. Install Tesseract and upload a page image or enable PDF OCR.'},status=422)
                except ImportError: return Response({'detail':'PDF text extraction requires PyMuPDF. Install pymupdf, or upload a JPG/PNG invoice.'},status=501)
            else:
                try:
                    from PIL import Image
                    import pytesseract
                    import io
                    text=pytesseract.image_to_string(Image.open(io.BytesIO(upload.read())))
                except ImportError: return Response({'detail':'Image OCR requires Pillow and pytesseract plus the Tesseract OCR engine. See README.'},status=501)
                except Exception as exc: return Response({'detail':f'OCR failed. Check that Tesseract is installed and configured. {str(exc)[:180]}'},status=422)
        except Exception as exc: return Response({'detail':f'Could not read invoice: {str(exc)[:180]}'},status=422)
        import re
        amounts=re.findall(r'(?:₹|INR|Rs\.?\s*)\s*([0-9,]+(?:\.[0-9]{1,2})?)',text,re.I)
        date_match=re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',text)
        return Response({'extracted_text':text[:12000],'candidate_amounts':[a.replace(',','') for a in amounts[-10:]],'candidate_date':date_match.group(1) if date_match else None,'matched_products':[],'workflow':'Review extracted data, match products and confirm before saving a purchase. OCR output is a draft and must be verified.','auto_imported':False})
