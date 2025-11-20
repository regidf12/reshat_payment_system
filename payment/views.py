from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
import stripe
from .models import Item
from django.conf import settings
from .models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


def index(request):
    items = Item.objects.all()
    return render(request, 'index.html', {'items': items})

def item_page(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    currency = request.GET.get('currency', item.currency).lower()
    if currency not in ['usd', 'eur']:
        currency = 'usd'

    display_price = float(item.price)
    if item.currency == 'usd' and currency == 'eur':
        display_price = round(display_price * 0.92, 2)
    elif item.currency == 'eur' and currency == 'usd':
        display_price = round(display_price * 1.09, 2)
    
    return render(request, "item_page.html", {
        "item": item,
        "display_price": display_price,
        "currency": currency,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY if currency == 'eur' else settings.STRIPE_PUBLIC_KEY,
    })

def buy(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.currency == "usd":
        stripe.api_key = settings.STRIPE_SECRET_KEY
    elif item.currency == "eur":
        stripe.api_key = settings.STRIPE_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price_data': {
            'currency': item.currency,
            'product_data': {
                'name': item.name,
            },
            'unit_amount': int(item.price * 100),
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
    total = sum(item.price for item in items)
    currency = 'usd'
    return render(request, "order.html", {"items": items, "total": total, "currency": currency})

def checkout(request):
    cart = request.session.get('cart', [])
    items = Item.objects.filter(id__in=cart)
    order = Order.objects.create()
    order.items.set(items)
    line_items = [{
        'price_data': {
            'currency': item.currency,
            'product_data': {'name': item.name},
            'unit_amount': int(item.price * 100),
        },
        'quantity': 1
    } for item in items]
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri('/success/'),
        cancel_url=request.build_absolute_uri('/cart/')
    )
    return redirect(session.url)

def clear_cart(request):
    request.session['cart'] = []
    return redirect('index')

def payment_success(request):
    request.session['cart'] = []
    return render(request, "success.html")
