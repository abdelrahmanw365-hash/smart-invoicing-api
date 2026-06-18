from django.contrib import admin
from .models import Product, Client, Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # These names MUST exist in Step 1
    list_display = ('invoice_number', 'client', 'total', 'status', 'date_created')
    readonly_fields = ('invoice_number', 'total', 'date_created')
    inlines = [InvoiceItemInline]

# Make sure these are registered too
# admin.site.register(Product)
# admin.site.register(Client)