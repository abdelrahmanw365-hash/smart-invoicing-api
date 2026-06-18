from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.views import APIView
from django.db.models import F, Sum
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa

from .models import Product, Client, Invoice, InvoiceItem, Expense
from .serializers import ProductSerializer, ClientSerializer, InvoiceCreateSerializer, InvoiceListSerializer, \
    ExpenseSerializer


class ProductViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_products = Product.objects.filter(stock__lte=F('low_stock_threshold'))
        serializer = self.get_serializer(low_products, many=True)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    permission_classes = []
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


class InvoiceViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []

    def list(self, request):
        invoices = Invoice.objects.all()
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = InvoiceCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                invoice = serializer.save()
                return Response({
                    "message": "Invoice created successfully!",
                    "invoice_number": invoice.invoice_number,
                    "total": invoice.total
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 📈 UPGRADED DASHBOARD WITH PROFIT ANALYTICS!
class DashboardAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # 1. Total Revenue (Sales)
        revenue = Invoice.objects.aggregate(Sum('total'))['total__sum'] or Decimal('0.00')

        # 2. Cost of Goods Sold (COGS)
        total_cogs = Decimal('0.00')
        for item in InvoiceItem.objects.all():
            total_cogs += (item.product.cost_price * Decimal(str(item.quantity)))

        # 3. Total Expenses
        total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        # 4. Net Profit = Revenue - COGS - Expenses
        net_profit = revenue - total_cogs - total_expenses

        total_invoices = Invoice.objects.count()
        low_stock_count = Product.objects.filter(stock__lte=F('low_stock_threshold')).count()

        return Response({
            "total_revenue": revenue,
            "total_cogs": total_cogs,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "total_invoices": total_invoices,
            "low_stock_alerts": low_stock_count
        })


@api_view(['GET'])
def generate_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    items = []
    for item in invoice.items.all():
        items.append({
            'name': item.product.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total_price': item.quantity * item.unit_price
        })

    template = get_template('invoice_pdf.html')
    html = template.render({'invoice': invoice, 'items': items})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('We had some errors generating your PDF!')
    return response