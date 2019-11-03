from django.db import models

from django.conf import settings
from products.models import Product
from django.db.models.signals import pre_save, post_save, m2m_changed

User = settings.AUTH_USER_MODEL

# Create your models here.

class CartManager(models.Manager):

    def new_or_get(self, request):
        # This method takes the request and either creates a new cart object or returns the existing one
        # Along with a boolean signifying the created/existing status
        cart_id = request.session.get("cart_id", None)      # returns the current cart_id else None

        qs = self.get_queryset().filter(id=cart_id)
        if qs.count() == 1:
            new_obj = False
            print('Existing cart_id found')
            cart_obj = qs.first()
            if request.user.is_authenticated() and cart_obj.user is None:
                cart_obj.user = request.user
                cart_obj.save()
        else:
            new_obj = True
            cart_obj = self.new(user=request.user)
            request.session['cart_id'] = cart_obj.id
        return cart_obj, new_obj

    def new(self, user=None):
        print('Creating new cart')
        user_obj = None
        if user is not None:
            if user.is_authenticated():
                user_obj = user
        return self.model.objects.create(user=user_obj)

class Cart(models.Model):
    user            = models.ForeignKey(User, null=True, blank=True)    # keeps a track of user
    products        = models.ManyToManyField(Product, blank=True)       # keeps a of products
    sub_total       = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    total           = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    updated         = models.DateTimeField(auto_now=True)                 # keeps a track of last cart update
    timestamp       = models.DateTimeField(auto_now_add=True)           # keeps a track of cart initialization

    objects = CartManager()

    def __str__(self):
        return str(self.id)

    @property
    def name(self):
        return self.title


def m2m_changed_cart_receiver(sender, instance, action, *args, **kwargs):
    if 'post' in action:
        products = instance.products.all()
        total = 0
        
        for x in products:
            total += x.price
        
        if instance.sub_total != total:
            instance.sub_total = total
            instance.save()

def pre_save_cart_receiver(sender, instance, *args, **kwargs):
    if instance.sub_total > 0:
        instance.total = float(instance.sub_total) * float(1.075)   # add 7.5% tax
    else:
        instance.total = 0.00
    
m2m_changed.connect(m2m_changed_cart_receiver, sender=Cart.products.through)
pre_save.connect(pre_save_cart_receiver, sender=Cart)