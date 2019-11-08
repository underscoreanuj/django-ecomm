from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save, post_save

from .signals import object_viewed_signal
from .utils import get_client_ip

from accounts.signals import user_logged_in_signal


User = settings.AUTH_USER_MODEL


FORCE_SESSION_TO_ONE = getattr(settings, 'FORCE_SESSION_TO_ONE', False)
FORCE_INACTIVE_USER_END_SESSION = getattr(settings, 'FORCE_INACTIVE_USER_END_SESSION', False)


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


class UserSession(models.Model):
    user            = models.ForeignKey(User, blank=True, null=True)        # User instance
    ip_address      = models.CharField(max_length=220, blank=True, null=True)
    session_key     = models.CharField(max_length=100, blank=True, null=True)
    timestamp       = models.DateTimeField(auto_now_add=True)
    active          = models.BooleanField(default=True)
    ended           = models.BooleanField(default=False)

    def end_session(self):
        try:
            Session.objects.get(pk=self.session_key).delete()
            self.active = False
            self.ended = True
            self.save()
        except Exception as e:
            pass

        return self.ended


def post_save_session_receiver(sender, instance, created, *args, **kwargs):
    if created:
        qs = UserSession.objects.filter(user=instance.user).exclude(id=instance.id)
        for i in qs:
            i.end_session()
    if not instance.active and not instance.ended:
        instance.end_session()


def post_save_user_changed_receiver(sender, instance, created, *args, **kwargs):
    if not created:
        if not instance.is_active:
            qs = UserSession.objects.filter(user=instance.user).exclude(id=instance.id)
            for i in qs:
                i.end_session()


def object_viewed_receiver(sender, instance, request, *args, **kwargs):
    new_view_obj = ObjectViewed.objects.create(
        user=request.user,
        ip_address=get_client_ip(request),
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.id
    )


def user_logged_in_receiver(sender, instance, request, *args, **kwargs):
    new_user_session_obj = UserSession.objects.create(
        user=instance,
        ip_address=get_client_ip(request),
        session_key=request.session.session_key
    )


object_viewed_signal.connect(object_viewed_receiver)
user_logged_in_signal.connect(user_logged_in_receiver)

if FORCE_SESSION_TO_ONE:
    post_save.connect(post_save_session_receiver, sender=UserSession)
if FORCE_INACTIVE_USER_END_SESSION:
    post_save.connect(post_save_user_changed_receiver, sender=User)
