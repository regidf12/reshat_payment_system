from decimal import Decimal

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

import stripe

from .models import Discount, Item, Order, Tax

stripe.api_key = settings.STRIPE_SECRET_KEY

SUPPORTED_CURRENCIES = ('usd', 'eur')


def get_stripe_public_key(currency: str) -> str:
    attr = f'STRIPE_PUBLIC_KEY_{currency.upper()}'
    return getattr(settings, attr, settings.STRIPE_PUBLIC_KEY)


def get_stripe_secret_key(currency: str) -> str:
    attr = f'STRIPE_SECRET_KEY_{currency.upper()}'
    return getattr(settings, attr, settings.STRIPE_SECRET_KEY)


def convert_price(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    if from_currency == to_currency:
        return amount
    rates = {
        ('usd', 'eur'): Decimal('0.92'),
        ('eur', 'usd'): Decimal('1.09'),
    }
    rate = rates.get((from_currency, to_currency))
    if rate is None:
        return amount
    return (Decimal(amount) * rate).quantize(Decimal('0.01'))


def index(request):
    items = Item.objects.all()
    return render(request, 'index.html', {'items': items})

def item_page(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    currency = request.GET.get('currency', item.currency).lower()
    if currency not in SUPPORTED_CURRENCIES:
        currency = item.currency

    display_price = convert_price(item.price, item.currency, currency)
    stripe_key = get_stripe_public_key(currency)
    
    return render(request, "item_page.html", {
        "item": item,
        "display_price": display_price,
        "currency": currency,
        "stripe_public_key": stripe_key,
    })

def buy(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    currency = request.GET.get('currency', item.currency).lower()
    if currency not in SUPPORTED_CURRENCIES:
        currency = item.currency

    amount = convert_price(item.price, item.currency, currency)
    unit_amount = int((amount * Decimal('100')).quantize(Decimal('1')))

    stripe.api_key = get_stripe_secret_key(currency)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {
                    'name': item.name,
                },
                'unit_amount': unit_amount,
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri(f'/item/{item.id}?bought=0')
    )
    return JsonResponse({'session_id': session.id})

def create_payment_intent(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    intent = stripe.PaymentIntent.create(
        amount=int(item.price * 100),
        currency=item.currency,
        metadata={"item_id": item.id}
    )
    return JsonResponse({"clientSecret": intent.client_secret})

def add_to_cart(request, item_id):
    cart = request.session.get('cart', [])
    if item_id not in cart:
        cart.append(item_id)
        request.session['cart'] = cart
    return redirect('index')

def cart_view(request):
    cart = request.session.get('cart', [])
    items = Item.objects.filter(id__in=cart)
    currency = request.POST.get('currency') or request.GET.get('currency', 'usd')
    if currency not in SUPPORTED_CURRENCIES:
        currency = 'usd'

    if request.method == 'POST':
        discount_id = request.POST.get('discount_id') or None
        tax_id = request.POST.get('tax_id') or None
        request.session['cart_discount_id'] = int(discount_id) if discount_id else None
        request.session['cart_tax_id'] = int(tax_id) if tax_id else None
        url = f"{reverse('cart')}?currency={currency}"
        return redirect(url)

    selected_discount_id = request.session.get('cart_discount_id')
    selected_tax_id = request.session.get('cart_tax_id')

    cart_items = []
    total = Decimal('0.00')
    for item in items:
        price_converted = convert_price(item.price, item.currency, currency)
        cart_items.append({
            "name": item.name,
            "price": price_converted.quantize(Decimal('0.01'))
        })
        total += price_converted

    total = total.quantize(Decimal('0.01')) if cart_items else Decimal('0.00')

    context = {
        "items": items,
        "cart_items": cart_items,
        "total": total,
        "currency": currency,
        "discounts": Discount.objects.all(),
        "taxes": Tax.objects.all(),
        "selected_discount_id": selected_discount_id,
        "selected_tax_id": selected_tax_id,
    }
    return render(request, "order.html", context)

def checkout(request):
    cart = request.session.get('cart', [])
    items = Item.objects.filter(id__in=cart)
    currency = request.GET.get('currency', 'usd').lower()
    if currency not in SUPPORTED_CURRENCIES:
        currency = 'usd'

    discount = None
    tax = None
    discount_id = request.session.get('cart_discount_id')
    tax_id = request.session.get('cart_tax_id')
    if discount_id:
        discount = Discount.objects.filter(id=discount_id).first()
    if tax_id:
        tax = Tax.objects.filter(id=tax_id).first()

    order = Order.objects.create(discount=discount, tax=tax)
    order.items.set(items)

    line_items = []
    for item in items:
        price_converted = convert_price(item.price, item.currency, currency)
        line_item = {
            'price_data': {
                'currency': currency,
                'product_data': {'name': item.name},
                'unit_amount': int((price_converted * Decimal('100')).quantize(Decimal('1'))),
            },
            'quantity': 1,
        }
        if tax and tax.stripe_tax_rate_id:
            line_item['tax_rates'] = [tax.stripe_tax_rate_id]
        line_items.append(line_item)

    session_params = {
        'payment_method_types': ['card'],
        'line_items': line_items,
        'mode': 'payment',
        'success_url': request.build_absolute_uri('/success/'),
        'cancel_url': request.build_absolute_uri(f'/cart/?currency={currency}')
    }

    if discount and discount.stripe_coupon_id:
        session_params['discounts'] = [{'coupon': discount.stripe_coupon_id}]

    stripe.api_key = get_stripe_secret_key(currency)
    session = stripe.checkout.Session.create(**session_params)

    return redirect(session.url)

def clear_cart(request):
    request.session['cart'] = []
    request.session['cart_discount_id'] = None
    request.session['cart_tax_id'] = None
    return redirect('index')

def payment_success(request):
    request.session['cart'] = []
    request.session['cart_discount_id'] = None
    request.session['cart_tax_id'] = None
    return render(request, "success.html")
