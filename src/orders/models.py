from django.db import models

from django.db.models.signals import pre_save, post_save
from carts.models import Cart
from billing.models import BillingProfile
from ecommerce.utils import unique_order_id_generator
from addresses.models import Address
import math


# Create your models here.

ORDER_STATUS_CHOICES = (
#     stored,   display
    ('created', 'Created'),
    ('paid', 'Paid'),
    ('shipped', 'Shipped'),
    ('refunded', 'Refunded'),
)

class OrderManager(models.Manager):
    def new_or_get(self, billing_profile, cart_obj):
        created = False
        qs = self.get_queryset().filter(billing_profile=billing_profile, cart=cart_obj, active=True, status="created")
        if qs.count() == 1:
            obj = qs.first()
        else:
            # create the order object
            obj = self.model.objects.create(billing_profile=billing_profile, cart=cart_obj)
            created = True
        
        return obj, created

class Order(models.Model):
    order_id                = models.CharField(max_length=120, blank=True)      # must be random and unique
    billing_profile         = models.ForeignKey(BillingProfile, null=True, blank=True)
    shipping_address        = models.ForeignKey(Address, related_name="shipping_address", null=True, blank=True)
    billing_address         = models.ForeignKey(Address, related_name="billing_address", null=True, blank=True)
    cart                    = models.ForeignKey(Cart)
    shipping_total          = models.DecimalField(default=40.00, max_digits=100, decimal_places=2)
    total                   = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    status                  = models.CharField(max_length=120, default='created', choices=ORDER_STATUS_CHOICES)
    active                  = models.BooleanField(default=True)

    objects = OrderManager()

    def __str__(self):
        return self.order_id

    def update_total(self):
        cart_total = self.cart.total
        shipping_total = self.shipping_total
        new_total = math.fsum([cart_total, shipping_total])
        formatted_total = format(new_total, '.2f')
        self.total = formatted_total
        self.save()
        return formatted_total    

    def check_done(self):
        billing_profile = self.billing_profile
        billing_address = self.billing_address
        shipping_address = self.shipping_address
        total = self.total

        if billing_profile and billing_address and shipping_address and total > 0:
            return True

        return False

    def mark_paid(self):
        if self.check_done():
            self.status = "paid"
            self.save()

        return self.status

        

def pre_save_create_order_id(sender, instance, *args, **kwargs):
    if not instance.order_id:
        instance.order_id = unique_order_id_generator(instance)
    
    # find and de-activate existing cart orders with older billing profiles
    qs = Order.objects.filter(cart=instance.cart).exclude(billing_profile=instance.billing_profile)
    if qs.exists():
        qs.update(active=False)


def post_save_order(sender, instance, created, *args, **kwargs):
    """
    calculate the total when the order id first created
    """
    if created:
        instance.update_total()

def post_save_cart_total(sender, instance, created, *args, **kwargs):
    """
    updates the Order if the cart is changed
    """
    if not created:
        cart_obj = instance
        cart_total = cart_obj.total
        cart_id = cart_obj.id

        qs = Order.objects.filter(cart__id=cart_id)                 # lookup for the associated cart object
        if qs.count() == 1:
            order_obj = qs.first()
            order_obj.update_total()

pre_save.connect(pre_save_create_order_id, sender=Order)
post_save.connect(post_save_cart_total, sender=Cart)
post_save.connect(post_save_order, sender=Order)
    