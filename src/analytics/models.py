from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


User = settings.AUTH_USER_MODEL


class ObjectViewed(models.Model):
    user            = models.ForeignKey(User, blank=True, null=True)        # User instance
    ip_address      = models.CharField(max_length=220, blank=True, null=True)
    content_type    = models.ForeignKey(ContentType)                        # User   , Product,    Order, Cart, Address
    object_id       = models.PositiveIntegerField()                         # User id, Product id, Order id, etc
    content_object  = GenericForeignKey('content_type', 'object_id')        # corresponding instance for the model's id
    timestamp       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s viewed on: %s" %(self.content_object, self.timestamp)

    class Meta:
        ordering = ['-timestamp']               # - for reverse timestamp ordering (most recent on the top)
        verbose_name = 'Object viewed'
        verbose_name_plural = 'Objects viewed'
