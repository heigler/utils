#_*- coding: utf-8 -*-
#DJANGO
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
#HELPERS
from utils.generic_accounts.helpers import gen_random_code 


class CommonTkt(models.Model):
    user = models.ForeignKey(User, unique=True)
    key = models.CharField(max_length=200, unique=True)
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return self.user.username    


class Tkt(CommonTkt):
    referer = models.IntegerField(null=True, blank=True)
    
    def get_absolute_url(self, request):
        return 'http://%s%s' %(request.META['HTTP_HOST'], reverse('account_confirm', args=[self.key]))


class RecoveryTkt(CommonTkt):
    
    def save(self):
        self.key = gen_random_code()
        super(RecoveryTkt, self).save()
    
    def get_absolute_url(self, request):
        return 'http://%s%s' %(request.META['HTTP_HOST'], reverse('account_recovery_confirm', args=[self.key]))
    
        
    
def user_post_save(signal, instance, sender, created, **kwargs):
    if created:
        tkt = Tkt(user=instance, key=gen_random_code())
        tkt.save()
    
signals.post_save.connect(user_post_save, sender=User)