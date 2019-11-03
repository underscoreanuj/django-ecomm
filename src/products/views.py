from django.shortcuts import render, get_object_or_404
from django.http import Http404

from django.views.generic import ListView, DetailView
from .models import Product
from carts.models import Cart

# Create your views here.

class ProductFeaturedListView(ListView):
    template_name = "products/product_list.html"

    # overriding the Product.objects.all()
    def get_queryset(self, *args, **kwargs):
        request = self.request
        return Product.objects.all().featured()

class ProductFeaturedDetailView(DetailView):
    # queryset = Product.objects.all()
    template_name = "products/featured_product_detail.html"

    # overriding the Product.objects.all()
    def get_queryset(self, *args, **kwargs):
        request = self.request
        return Product.objects.all().featured()


class ProductListView(ListView):
    # queryset = Product.objects.all()
    template_name = "products/product_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ProductListView, self).get_context_data(*args, **kwargs)
        cart_obj, new_obj = Cart.objects.new_or_get(self.request)
        context['cart'] = cart_obj
        return context

    # overriding the Product.objects.all()
    def get_queryset(self, *args, **kwargs):
        request = self.request
        return Product.objects.all()

        
def product_list_view(request):
    queryset = Product.objects.all()
    context = {
        "object_list": queryset
    }
    return render(request, "products/product_list.html", context)

class ProductDetailView(DetailView):
    # queryset = Product.objects.all()
    template_name = "products/product_detail.html"
    def get_context_data(self, *args, **kwargs):
        context = super(ProductDetailView, self).get_context_data(*args, **kwargs)
        # print(context)
        return context

    # overriding the Product.object.all()
    def get_object(self, *args, **kwargs):
        request = self.request
        pk = self.kwargs.get('pk')

        instance = Product.objects.get_by_id(pk)
        if instance is None:
            raise Http404("Product does NOT exist!")

        return instance

        
def product_detail_view(request, pk=None, *args, **kwargs):
    # print(args)
    # print(kwargs)
    # instance = Product.objects.get(pk=pk)                         # id=pk  will also work

    # instance = get_object_or_404(Product, pk=pk)
    
    # manual alternative of the get_object_or_404 function
    '''
    try:
        instance = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        print("Product does not exist!")
        raise Http404("Product Does NOT Exist!")
    except:
        print("??")
    '''

    # another way
    # qs = Product.objects.filter(pk=pk)
    # if the qs is not None and has a length of 1 element
    # if qs.exists() and qs.count() == 1:
        # instance = qs.first()
    # else:
        # raise Http404("Product Does NOT Exist!")

    # Yet another way 
    # this one employs the use of a custom filter
    instance = Product.objects.get_by_id(pk)
    # print(instance)
    if instance is None:
        raise Http404("Product does NOT exist!")

    context = {
        "object": instance
    }
    return render(request, "products/product_detail.html", context)
 

class ProductDetailSlugView(DetailView):
    queryset = Product.objects.all()
    template_name = "products/product_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super(ProductDetailSlugView, self).get_context_data(*args, **kwargs)
        cart_obj, create_bool = Cart.objects.new_or_get(self.request)
        context['cart'] = cart_obj
        return context

    def get_object(self, *args, **kwargs):
        request = self.request
        slug = self.kwargs.get('slug')
        # instance = get_object_or_404(Product, slug=slug, active=True)
        try:
            instance = Product.objects.get(slug=slug, active=True)
        except Product.DoesNotExist:
            raise Http404("Nothing Found!")
        except Product.MultipleObjectsReturned:
            qs = Product.objects.filter(slug=slug, active=True)
            instance = qs.first()
        except:
            raise Http404("Nothing Found hmmmmm!")
        
        return instance