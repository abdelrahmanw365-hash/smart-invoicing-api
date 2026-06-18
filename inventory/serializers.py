from rest_framework import serializers
from .models import Product, Client, Invoice, InvoiceItem, Expense
from .services import create_invoice_flow


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class InvoiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


class InvoiceItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()


class InvoiceCreateSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    items = InvoiceItemCreateSerializer(many=True)
    payment_method = serializers.CharField(max_length=15, default='CASH')
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def create(self, validated_data):
        from .models import Client, Product
        client = Client.objects.get(id=validated_data['client_id'])

        items_data = []
        for item in validated_data['items']:
            product = Product.objects.get(id=item['product_id'])
            items_data.append({'product': product, 'quantity': item['quantity']})

        return create_invoice_flow(
            client=client,
            items_data=items_data,
            payment_method=validated_data.get('payment_method', 'CASH'),
            amount_paid=validated_data.get('amount_paid', 0.00)
        )