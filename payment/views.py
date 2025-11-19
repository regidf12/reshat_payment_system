from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import stripe
from .models import Item
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def index(request):
    items = Item.objects.all()
    return render(request, 'index.html', {'items': items})

def item_page(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    return render(request, "item_page.html", {
        "item": item,
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
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
    success_url=request.build_absolute_uri(f'/item/{item.id}?bought=1'),
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
