from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Invoice, InvoiceItem, Product


def create_invoice_flow(client, items_data, payment_method='CASH', amount_paid=0.00):
    """
    Secure transaction-wrapped checkout flow.
    Calculates VAT authoritatively server-side (14%).
    Locks product records during execution to prevent race conditions.
    """
    # Authoritative Egypt VAT Rate
    VAT_RATE = Decimal('14.00')

    with transaction.atomic():
        # 1. Lock the product database rows using select_for_update() to prevent race conditions
        product_ids = [item['product_id'] for item in items_data]
        locked_products = {
            p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)
        }

        # 2. Initialize the base invoice with temporary zero sums
        invoice = Invoice.objects.create(
            client=client,
            payment_method=payment_method,
            amount_paid=Decimal(str(amount_paid))
        )

        running_subtotal = Decimal('0.00')
        running_total_discount = Decimal('0.00')
        running_total_vat = Decimal('0.00')

        # 3. Process line items under database lock
        for item in items_data:
            prod_id = item['product_id']
            qty = Decimal(str(item['quantity']))
            disc_rate = Decimal(str(item.get('discount_rate', 0.00)))

            product = locked_products.get(prod_id)
            if not product:
                raise ValidationError(f"Product ID {prod_id} does not exist.")

            # 🪄 Authoritative Stock Validation (Server-side)
            if product.stock < item['quantity']:
                raise ValidationError(
                    f"Transaction aborted: Not enough stock for {product.name}. "
                    f"Requested: {item['quantity']}, Available: {product.stock}"
                )

            # Deduct inventory safely
            product.stock -= item['quantity']
            product.save()

            # Dynamic price calculations (Authoritative)
            price = product.selling_price
            subtotal_line = price * qty

            discount_line = subtotal_line * (disc_rate / Decimal('100'))
            taxable_line = subtotal_line - discount_line

            # Force authoritative 14% VAT computation
            vat_line = taxable_line * (VAT_RATE / Decimal('100'))
            total_line = taxable_line + vat_line

            # Save line item record
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=item['quantity'],
                unit_price=price,
                discount_rate=disc_rate,
                vat_rate=VAT_RATE,
                discount_amount=discount_line,
                vat_amount=vat_line,
                total_price=total_line
            )

            # Update running calculations
            running_subtotal += subtotal_line
            running_total_discount += discount_line
            running_total_vat += vat_line

        # 4. Calculate grand total
        running_total = (running_subtotal - running_total_discount) + running_total_vat

        # 🪄 Validate Payment Methods & Underpayments
        paid_amount = Decimal(str(amount_paid))
        if payment_method == 'CASH' and paid_amount < running_total:
            raise ValidationError(
                f"Validation Error: Amount Paid (${paid_amount}) cannot be less than "
                f"Total Due (${running_total}) for Cash transactions."
            )

        # Determine Payment Status
        if paid_amount >= running_total:
            status = 'PAID'
        elif paid_amount > 0:
            status = 'PARTIAL'
        else:
            status = 'UNPAID'

        # 5. Finalize invoice financial calculations
        invoice.subtotal = running_subtotal
        invoice.total_discount = running_total_discount
        invoice.total_vat = running_total_vat
        invoice.total = running_total
        invoice.status = status
        invoice.save()

        return invoice