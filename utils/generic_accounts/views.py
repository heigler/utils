#-*- coding: utf-8 -*-
#DJANGO
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import simple, create_update
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
#HELPERS
from utils.generic.views import CreateObjectView, UpdateObjectView, generic_user_login
from utils.generic_accounts.forms import RegisterForm, ChangePasswordForm, RecoveryTktForm
from utils.generic_accounts.models import Tkt, RecoveryTkt
from utils.generic_accounts.helpers import gen_random_code
from utils.mail import send_html_mail


class CreateRegister(CreateObjectView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    
    def __call__(self, request):  
        
        self.post_save_redirect = reverse('account_register_ok')
        self.request = request
        return super(CreateRegister, self).__call__(request)
    
 
    def save_instance(self, obj):        
        obj.is_active = False
        obj.set_password(self.form.cleaned_data['password'])
        super(CreateRegister, self).save_instance(obj)        
        
        tkt = Tkt.objects.get(user=obj)
        referer = request.GET.get('ref', None)
        if referer:
            try:
                tkt.referer = int(referer)
                tkt.save()
            except ValueError:
                pass
            
        
        #Sends the email here
        email_context = {'username': obj.username,
                         'password': self.form.cleaned_data.get('password',''),
                         'activation_link': tkt.get_absolute_url(self.request)}
        
        send_html_mail(to = obj.email,
                       tmpl_basename = 'accounts/email/default',
                       context = email_context,
                       subject = _('Account activation')
                       )


register = CreateRegister()



def register_confirm(request, key):
    tkt = get_object_or_404(Tkt, key=key)
    
    #Activate the user
    user = User.objects.get(username=tkt.user.username)
    user.is_active = True
    user.save()
    
    tkt.delete()
    
    #Make login
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    
    response = simple.direct_to_template(request,
                                         template = 'accounts/confirm_ok.html')
    
    return response



def user_logout(request):
    logout(request)
    to = '/'
    
    return HttpResponseRedirect(to)



class CreateChangePassword(UpdateObjectView):
    form_class = ChangePasswordForm
    login_required = True
    template_name = 'accounts/change_password.html'   
    
    def __call__(self, request):
        self.object_id = request.user.id
        self.post_save_redirect = reverse('account_change_pass_ok')
        return super(CreateChangePassword, self).__call__(request)
    
    def save_instance(self, obj):
        obj.set_password(self.form.cleaned_data['password'])
        super(CreateChangePassword, self).save_instance(obj)

change_password = CreateChangePassword()
    
    

def recovery_password(request):
    if request.method == 'POST':
        form = RecoveryTktForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get('email', '')
            user = User.objects.get(email=email)
            
            try:
                #If there is a tkt, generate a new key
                tkt = RecoveryTkt.objects.get(user=user)
            except RecoveryTkt.DoesNotExist:               
                tkt = RecoveryTkt(user=user)
                
            tkt.save()
            
            email_context = {'user': user,
                             'recovery_link': tkt.get_absolute_url(request)
                             }
            
            send_html_mail(to = email,
                           tmpl_basename = 'accounts/email/recovery',
                           context = email_context,
                           subject = _('Account recovery - Confirmation')
                           )
                           
            return HttpResponseRedirect(reverse('account_recovery_ok'))
        
    else:
        form = RecoveryTktForm()
            
    response = simple.direct_to_template(request,
                                         template = 'accounts/recovery.html',
                                         extra_context = {'form': form})
        
    return response
        

def recovery_confirm(request, key):
    tkt = get_object_or_404(RecoveryTkt, key=key)
    
    user = User.objects.get(username=tkt.user.username)
    new_pass = gen_random_code()[:8]
    user.set_password(new_pass)
    user.save()
    
    tkt.delete()
   
    email_context = {'user': user,
                     'new_pass': new_pass}
    
    send_html_mail(to = user.email,
                   tmpl_basename = 'accounts/email/recovery_confirm',
                   context = email_context,
                   subject = _('Account recovery - New password'))
    
    response = simple.direct_to_template(request,
                                         template = 'accounts/recovery_confirm.html')
    
    return response
           


def user_login(request):
    response = generic_user_login(request)
                                  
    return response



