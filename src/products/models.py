import random
import os
import time
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.urls import reverse
from ecommerce.utils import unique_slug_generator
from django.db.models import Q              # used to perform better lookups, by encapsulating multiple filters

# takes the file path and returns the file's name & extension
def get_filename_ext(filepath):
    base_name = os.path.basename(filepath)
    name, ext = os.path.splitext(base_name)
    return name, ext

# takes the instance along with the filename and renames it with a random integer in a large range
def upload_image_path(instance, filename):
    print(instance)
    print(filename)
    new_filename = random.randint(1, 91264681379731233)
    name, ext = get_filename_ext(filename)
    final_filename = '{ts}_{new_filename}{ext}'.format(ts=int(time.time()), new_filename=new_filename, ext=ext)
    return 'products/{ts}_{new_filename}/{final_filename}'.format(
        ts=int(time.time()), new_filename=new_filename, final_filename=final_filename
    )

class ProductQuerySet(models.query.QuerySet):
    def featured(self):
        return self.filter(featured=True, active=True)
    
    def active(self):
        return self.filter(active=True)

    def search(self, query):
        lookups = (Q(title__icontains=query) |
                   Q(description__icontains=query) |
                   Q(price__icontains=query) |
                   Q(tag__title__icontains=query))
        # distinct helps remove redundancy from lookups which mactch for multiple filters
        return self.filter(lookups).distinct()

class ProductManager(models.Manager):
    def get_by_id(self, id):
        qs = self.get_queryset().filter(id=id)      # Product.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def featured(self):
        return self.get_queryset().featured()

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset().active()

    def search(self, query):
        return self.get_queryset().active().search( query)

# Create your models here.
class Product(models.Model):
    title       = models.CharField(max_length=120)
    slug        = models.SlugField(blank=True, unique=True)
    description = models.TextField()
    price       = models.DecimalField(decimal_places=2, max_digits=20, default=0.00)
    image       = models.ImageField(upload_to=upload_image_path, null=True, blank=True)        # all uploads go to media_root (look settings.py)
    featured    = models.BooleanField(default=False)
    active      = models.BooleanField(default=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    # extend Product.objects to reference to our custom function instead of the default one
    objects = ProductManager()

    def get_absolute_url(self):
        # this statement is not robust as it takes into consideration that the
        # present url pattern is strictly 127.0.0.1:8000/products
        # hence it won't work if we intend to change it
        #
        # return "/products/{slug}/".format(slug=self.slug)
        
        # this statement on the other hand takes the url's name and returns the reverse value
        # which is calculated w.r.t the existing url in use
        # hence making it more robust and flexible
        return reverse('products:detail', kwargs={"slug": self.slug})

    def __str__(self):
        return self.title

def product_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)

pre_save.connect(product_pre_save_receiver, sender=Product)