#-*- coding: utf-8 -*-
#DJANGO
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.utils.translation import ugettext as _
#Helpers
from utils.formoptions import FormOptions

passwd_base_error = _('Passwords doesn\'t match')


class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(label='Primeiro nome', max_length=30)
    last_name = forms.CharField(label=u'Último nome', max_length=30)
    
    email = forms.EmailField()
    
    password = forms.CharField(label=u'Senha', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label=u'Confirme sua senha', widget=forms.PasswordInput)
    read_terms = forms.BooleanField(label=u'Declaro que li, entendi e aceito os termos de uso')
    
    def __init__(self, request, *args, **kwargs):
        ref = request.GET.get('ref', '')
        self.options = FormOptions(submit_label=u'Enviar', include_help_text=False, action='.?ref=%s'%ref, css_p_map={'read_terms': 'terms'})
    
        super(RegisterForm, self).__init__(*args, **kwargs)
    
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        
        
    def clean_confirm_password(self):
        confirm_passwd = self.cleaned_data['confirm_password']
        passwd = self.cleaned_data.get('password', confirm_passwd)
        
       
        if passwd != confirm_passwd:
            raise forms.ValidationError(passwd_base_error)
        
        return confirm_passwd
    
    
    def clean_email(self):
        email = self.cleaned_data['email']
        users = User.objects.filter(email=email)
        
        if users:
            raise forms.ValidationError(_('This email is already registered'))
        
        return email
        
        
        
class LoginForm(forms.Form):
    #Apenas seta os campos (Esse formulário pode ser estendido colocando outras opções de login,
    #como por exemplo um campo de e-mail)
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())

    options = FormOptions(submit_label=_('Login'))

    def clean(self):
        username = self.cleaned_data.get('username', '')
        password = self.cleaned_data.get('password', '')
        
        #O authenticate retorna o usuário ou None caso o login tenha falhado
        user = authenticate(username=username, password=password)

        #Exibe o erro em caso de falha de autenticação
        if user is None:
            raise forms.ValidationError(_('Login failed, check your data and try again.'))

        #Verifica se a conta está ativa, caso contrário exibe um erro de conta inativa
        if user:
            if not user.is_active:
                raise forms.ValidationError(_('Your account is not activated.'))

        #Seta o usuário no escopo global da classe (usaremos mais tarde no login propriamente dito)
        self.user = user

        return self.cleaned_data


    def u_login(self, request):
        #Verificamos se o form é válido (isso é equivalente a fazer form.is_valid() em uma view)
        if self.is_valid():
            
            #Por fim logamos o usuário
            login(request, self.user)
            return True

        return False



class ChangePasswordForm(forms.ModelForm):
    password = forms.CharField(label=_('New password'), widget=forms.PasswordInput)
    confirm_password = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput)
    
    options = FormOptions(submit_label=_('Change'), include_help_text=False)
    
    class Meta:
        model = User
        fields = ['password']
        
    def clean(self):
        cleaned = self.cleaned_data
        
        if cleaned.get('password', '') != cleaned.get('confirm_password', ''):
            raise forms.ValidationError(passwd_base_error)
        
        
        return cleaned


class ChangeUsernameForm(forms.ModelForm):   
    options = FormOptions(submit_label='Alterar', include_help_text=False)
    
    class Meta:
        model = User
        fields = ['username']        
       
        
class RecoveryTktForm(forms.Form):
    email = forms.EmailField()
    
    options = FormOptions(submit_label=_('Recovery'))
    
    def clean_email(self):
        email = self.cleaned_data.get('email', 'email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError(_('Nobory with that email was found.'))
        
        return email
