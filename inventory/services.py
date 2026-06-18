from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Invoice, InvoiceItem


def create_invoice_flow(client, items_data, payment_method='CASH', amount_paid=0.00):
    """
    items_data: list of dicts: [
        {'product': product_obj, 'quantity': int, 'discount_rate': Decimal, 'vat_rate': Decimal}, ...
    ]
    """
    with transaction.atomic():
        # 1. Create the base invoice shell
        invoice = Invoice.objects.create(
            client=client,
            payment_method=payment_method,
            amount_paid=Decimal(str(amount_paid))
        )

        running_subtotal = Decimal('0.00')
        running_total_discount = Decimal('0.00')
        running_total_vat = Decimal('0.00')
        running_total = Decimal('0.00')

        # 2. Process line items
        for item in items_data:
            product = item['product']
            qty = Decimal(str(item['quantity']))
            disc_rate = Decimal(str(item.get('discount_rate', 0.00)))
            vat_rate = Decimal(str(item.get('vat_rate', 14.00)))  # Default 14% Egypt VAT

            # Stock check
            if product.stock < item['quantity']:
                raise ValidationError(f"Not enough stock for {product.name}. Only {product.stock} left.")

            # Deduct inventory
            product.stock -= item['quantity']
            product.save()

            # Calculations
            price = product.selling_price
            subtotal_line = price * qty

            discount_line = subtotal_line * (disc_rate / Decimal('100'))
            taxable_line = subtotal_line - discount_line
            vat_line = taxable_line * (vat_rate / Decimal('100'))
            total_line = taxable_line + vat_line

            # Save line item
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=item['quantity'],
                unit_price=price,
                discount_rate=disc_rate,
                vat_rate=vat_rate,
                discount_amount=discount_line,
                vat_amount=vat_line,
                total_price=total_line
            )

            # Update running calculations
            running_subtotal += subtotal_line
            running_total_discount += discount_line
            running_total_vat += vat_line
            running_total += total_line

        # 3. Determine Payment Status
        paid_amount = Decimal(str(amount_paid))
        if paid_amount >= running_total:
            status = 'PAID'
        elif paid_amount > 0:
            status = 'PARTIAL'
        else:
            status = 'UNPAID'

        # 4. Finalize Invoice Details
        invoice.subtotal = running_subtotal
        invoice.total_discount = running_total_discount
        invoice.total_vat = running_total_vat
        invoice.total = running_total
        invoice.status = status
        invoice.save()

        return invoice