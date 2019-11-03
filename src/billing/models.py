from django.db import models

from django.conf import settings
from django.db.models.signals import post_save
from accounts.models import GuestEmail

# Create your models here.

User = settings.AUTH_USER_MODEL

class BillingProfileManager(models.Manager):
    def new_or_get(self, request):
        user = request.user
        guest_email_id = request.session.get("guest_email_id")
        created = False
        obj = None

        # if the user is logged in
        if user.is_authenticated():
            if user.email:
                obj, create_bool = self.model.objects.get_or_create(user=user, email=user.email)
        elif guest_email_id is not None:
            guest_email_obj = GuestEmail.objects.get(id=guest_email_id)
            obj, create_bool = self.model.objects.get_or_create(email=guest_email_obj.email)
        else:
            pass
        return obj, created

class BillingProfile(models.Model):
    user            = models.OneToOneField(User, null=True, blank=True)
    email           = models.EmailField()
    active          = models.BooleanField(default=True)
    updated         = models.DateTimeField(auto_now=True)
    timestamp       = models.DateTimeField(auto_now_add=True)

    objects = BillingProfileManager()

    def __str__(self):
        return self.email

"""
def billing_profile_created_receiver(sender, instance, created, *args, **kwargs):
    if created:
        print("Send to appropriate transaction gateway (API request)")
        instance.customer_id = newID
        instance.save()
"""

def user_created_receiver(sender, instance, created, *args, **kwargs):
    if created and instance.email:
        BillingProfile.objects.get_or_create(user=instance, email=instance.email)

# whenever a user gets created it will get a billing profile
post_save.connect(user_created_receiver, sender=User)

