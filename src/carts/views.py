from django.shortcuts import render, redirect
from django.http import JsonResponse

from .models import Cart
from products.models import Product
from orders.models import Order
from accounts.forms import LoginForm, GuestForm
from accounts.models import GuestEmail
from billing.models import BillingProfile
from addresses.forms import AddressForm
from addresses.models import Address

# Create your views here.

def cart_detail_api_view(request):
    cart_obj, new_obj = Cart.objects.new_or_get(request)
    products = [{
        "id": x.id,
        "url": x.get_absolute_url(),
        "title": x.title,
        "price": x.price
    }
        for x in cart_obj.products.all()]
    cart_data = {
        "products": products,
        "sub_total": cart_obj.sub_total,
        "total": cart_obj.total
    }
    return JsonResponse(cart_data)

def cart_home(request):
    cart_obj, create_bool = Cart.objects.new_or_get(request)

    return render(request, "carts/home.html", {"cart": cart_obj})


def cart_update(request):
    product_id = request.POST.get('product_id')

    if product_id is not None:
        try:
            product_obj = Product.objects.get(id=product_id)    
        except Product.DoesNotExist:
            print('product is no longer available!!!')
            return redirect('cart:home')
        
        cart_obj, create_bool = Cart.objects.new_or_get(request)

        if product_obj in cart_obj.products.all():
            cart_obj.products.remove(product_obj)
            product_added = False
        else:
            cart_obj.products.add(product_obj)                  # cart_obj.products.add(id) !!!also works
            product_added = True
        
        request.session['cart_items'] = cart_obj.products.count()

        if request.is_ajax():
            json_data = {
                "added": product_added,
                "removed": not product_added,
                "cartItemCount": cart_obj.products.count(),
            }
            return JsonResponse(json_data)

    return redirect('cart:home')


def checkout_home(request):
    cart_obj, create_bool = Cart.objects.new_or_get(request)
    order_obj = None
    
    # see if the cart is empty/created for the first time
    if create_bool or cart_obj.products.count() == 0:
        return redirect('cart:home')

    login_form = LoginForm()
    guest_form = GuestForm()
    address_form = AddressForm()
    billing_address_id = request.session.get("billing_address_id", None)
    shipping_address_id = request.session.get("shipping_address_id", None)
    
    billing_profile, billing_profile_create_bool = BillingProfile.objects.new_or_get(request)
    
    address_qs = None

    if billing_profile is not None:

        if request.user.is_authenticated():
            address_qs = Address.objects.filter(billing_profile=billing_profile)

        order_obj, order_obj_create_bool = Order.objects.new_or_get(billing_profile, cart_obj)

        if shipping_address_id:
            order_obj.shipping_address = Address.objects.get(id=shipping_address_id)
            del request.session["shipping_address_id"]
        if billing_address_id:
            order_obj.billing_address = Address.objects.get(id=billing_address_id)
            del request.session["billing_address_id"]
        
        # save the address if any one is given
        if billing_address_id or shipping_address_id:
            order_obj.save()

    if request.method == "POST":
        # verify that the order is done
        is_done = order_obj.check_done()
        if is_done:
            order_obj.mark_paid()
        
            # delete the cart from the session (since it is now processed)
            del request.session["cart_id"]
            request.session["cart_items"] = 0
        
            return redirect("cart:success")

    context = {
        "object": order_obj,
        "billing_profile": billing_profile,
        "login_form": login_form,
        "guest_form": guest_form,
        "address_form": address_form,
        "address_qs": address_qs
    }

    return render(request, "carts/checkout.html", context)

def checkout_done_view(request):
    return render(request, "carts/checkout_done.html", {})

