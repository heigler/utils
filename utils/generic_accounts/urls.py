#-*- coding: utf-8 -*-
from django.conf.urls.defaults import url, patterns
from django.views.generic import simple

urlpatterns = patterns('utils.generic_accounts.views',
    #Registration
    url(r'^register/$', 'register', name='account_register'),
    url(r'^register/ok/$', simple.direct_to_template, {'template': 'accounts/register_ok.html'},
        name='account_register_ok'),
    url(r'^register/confirm/(?P<key>[-\w]+)/$', 'register_confirm', name='account_confirm'), 
    
    #Management
    url(r'^logout/$', 'user_logout', name='account_logout'), 
    url(r'^login/$', 'user_login', name='account_login'),
    url(r'^change-password/$', 'change_password', name='account_change_pass'),
    url(r'^change-password/ok/$', simple.direct_to_template, {'template': 'accounts/change_password_ok.html'},
         name='account_change_pass_ok'),
    url(r'^recovery/$', 'recovery_password', name='account_recovery'),
    url(r'^recovery/ok/$', simple.direct_to_template, {'template': 'accounts/recovery_ok.html'},
         name='account_recovery_ok'),
    url(r'^recovery/confirm/(?P<key>[-\w]+)/$', 'recovery_confirm', name='account_recovery_confirm'),                           
                       
)