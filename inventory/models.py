from django.db import models
from django.utils.crypto import get_random_string


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Client(models.Model):
    CLIENT_TYPE_CHOICES = (
        ('B2B', 'Business (B2B)'),
        ('B2C', 'Individual Customer (B2C)'),
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    client_type = models.CharField(max_length=3, choices=CLIENT_TYPE_CHOICES, default='B2C')
    tax_id = models.CharField(max_length=9, blank=True, null=True)
    national_id = models.CharField(max_length=14, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.client_type})"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    eta_item_code = models.CharField(max_length=100, blank=True, null=True)
    stock = models.IntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_stock_threshold = models.IntegerField(default=5)

    def __str__(self):
        return f"{self.name} ({self.stock} left)"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('INSTALLMENT', 'Installment'),
        ('MIXED', 'Mixed Payment'),
    )
    ETA_STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to ETA'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )

    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNPAID')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='CASH')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    eta_status = models.CharField(max_length=10, choices=ETA_STATUS_CHOICES, default='DRAFT')
    eta_uuid = models.CharField(max_length=100, blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{get_random_string(5).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.00)

    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# 🔥 NEW: EXPENSE MODEL
class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('RENT', 'Rent'),
        ('SALARY', 'Salaries'),
        ('UTILITY', 'Utilities (Electricity/Water/Internet)'),
        ('MARKETING', 'Marketing'),
        ('OTHER', 'Other'),
    )

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - ${self.amount}"