#-*- coding: utf-8 -*-
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.utils import simplejson
from django.views.generic import simple
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import login
#HELPERS
from utils.generic_accounts.forms import LoginForm

class CreateObjectView(object):
    """
    Generic view to create instances of a model.

    """ 
    
    model = None
    form_class = None
    template_name = None
    extra_context = None
    post_save_redirect = None
        
    def __call__(self, request):
        """
        Create a new object using a ModelForm. Accepts arguments:

        ``request``
            The HttpRequest object.

        ``model``
            Model type to create (either this or form_class is
            required)

        ``form_class``
            ModelForm subclass to use (either this or model is
            required)

        ``template_name``
            name of template to use, or list of templates - defaults
            to <app_label>/<model_name>_form.html

        ``extra_context``
            dictionary of items and/or callables to add to template
            context.

        ``post_save_redirect``
            URL to redirect to after successful object save. If
            post_save_redirect is None or an empty string, default is
            to send to the instances get_absolute_url method or in its
            absence, the site root.

        """
        self.request = request
        (self.model, self.form_class) = self.get_model_and_form_class(
            self.model, self.form_class)
        self.form = self.get_form(request, self.form_class)
        if request.method == 'POST' and self.form.is_valid():
            return self.get_redirect(self.post_save_redirect, self.save_form(self.form))

        c = self.apply_extra_context(self.extra_context,
                                     self.get_context(request,
                                                      {'form': self.form}))
        t = self.get_template(self.model, self.template_name)
        return self.get_response(t, c)
    
    def get_model_and_form_class(self, _model, form_class):
        """
        Return a model and form class based on model or form_class
        argument.
        
        """
        if _model is None:
            try:
                _model = form_class._meta.model
            except AttributeError:
                raise ValueError("%s requires either model or form_class" %
                                 (self.__class__.__name__,))
        if form_class is None:
            class Meta:
                model = _model
            class_name = _model.__name__ + 'Form'
            form_class = forms.models.ModelFormMetaclass(
                class_name, (forms.ModelForm,), {'Meta': Meta})
        return (_model, form_class)

    def apply_extra_context(self, extra_context, context):
        """
        Add items from extra_context dict to the given context,
        calling any callables in extra_context.  Return the updated
        context.

        """
        extra_context = extra_context or {}
        for key, value in extra_context.iteritems():
            if callable(value):
                context[key] = value()
            else:
                context[key] = value
        return context

    def get_form_kwargs(self, request):
        """
        Get dictionary of arguments to construct the appropriate
        ``form_class`` instance.

        """
        if request.method == 'POST':
            return {'data': request.POST, 'files': request.FILES}
        return {}

    def get_form(self, request, form_class):
        """
        Return the appropriate ``form_class`` instance based on the
        ``request``.

        """
        return form_class(**self.get_form_kwargs(request))

    def save_instance(self, obj):
        """
        Save and return model instance.

        """
        obj.save()
        return obj
    
    def save_form(self, form):
        """
        Save form, returning saved object.

        """
        return self.save_instance(form.save(commit=False))
    
    def get_redirect(self, post_save_redirect, obj):
        """
        Return a HttpResponseRedirect based on ``post_save_redirect``
        argument and just-saved object ``obj``.

        """
        if not post_save_redirect:
            if hasattr(obj, 'get_absolute_url'):
                post_save_redirect = obj.get_absolute_url()
            else:
                post_save_redirect = "/"
        return HttpResponseRedirect(post_save_redirect)

    def get_template(self, model, template_name):
        """
        Return a template to use based on ``template_name`` and ``model``.

        """
        template_name = template_name or "%s/%s_form.html" % (
            model._meta.app_label, model._meta.object_name.lower())
        if isinstance(template_name, (list, tuple)):
            return loader.select_template(template_name)
        else:
            return loader.get_template(template_name)

    def get_context(self, request, dictionary):
        """
        Return a context instance with data in ``dictionary``.

        """
        return RequestContext(request, dictionary)
        
    def get_response(self, template, context_instance):
        """
        Return a HttpResponse object based on given request, template,
        and context.

        """
        return HttpResponse(template.render(context_instance))


class UpdateObjectView(CreateObjectView):
    """
    Generic view to update instances of a model.

    """
    
    object_id = None
    slug = None
    slug_field = 'slug'
    login_required = False
    
    def __call__(self, request, *args, **kwargs):
        """
        Update an existing object using a ModelForm.  Accepts same
        arguments as CreateObjectView, and also:

        ``object_id``
            id of object to update (either this or slug+slug_field is
            required)

        ``slug``
            slug of object to update (either this or object_id is
            required)

        ``slug_field``
            field to look up slug in (defaults to ``slug``)
        
        """
        if self.login_required and not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('account_login'))
        
        return super(UpdateObjectView, self).__call__(request, *args, **kwargs)
    
    def get_model_and_form_class(self, *args, **kwargs):
        """
        Wrap parent ``get_model_and_form_class`` and save the model
        class so we can get to it in get_form_args.

        """
        ret = super(UpdateObjectView, self).get_model_and_form_class(*args,
                                                                      **kwargs)
        self.model = ret[0]
        return ret

    def get_form_kwargs(self, request):
        instance = self.lookup_object(self.model, self.object_id,
                                      self.slug, self.slug_field)
        kwargs = super(UpdateObjectView, self).get_form_kwargs(request)
        kwargs['instance'] = instance
        return kwargs

    def lookup_object(self, model, object_id, slug, slug_field):
        """
        Find and return an object of type ``model`` based on either
        the given ``object_id`` or ``slug`` and ``slug_field``.
        
        """
        lookup_kwargs = {}
        if object_id:
            lookup_kwargs['%s__exact' % model._meta.pk.name] = object_id
        elif slug and slug_field:
            lookup_kwargs['%s__exact' % slug_field] = slug
        else:
            raise ValueError("%s requires object_id or slug+slug_field"
                             % (self.__class__.__name__,))
        try:
            return model.objects.get(**lookup_kwargs)
        except ObjectDoesNotExist:
            raise Http404, "No %s found for %s" % (model._meta.verbose_name,
                                                   lookup_kwargs)
        
       
 
def ajax_form_validate(request, form_class, success_message='ok'):
    """
    Generic view to renders a json object with the main error of a field.
    """
    
    if not request.is_ajax():
        return HttpResponseForbidden('Access denied!')
    
    field_name = request.POST['field_name']
    field_value = request.POST['field_value']     

    form_errors = form_class({field_name: field_value}).errors    

    try:
        field_message = unicode(form_errors[field_name][0])
        status = 'invalid'
    except KeyError:
        field_message = success_message
        status = 'valid'
       
    data = {'field_message': field_message,
            'status': status}
        
    response = HttpResponse()
    simplejson.dump(data, response)
    
    return response      



def generic_user_login(request, template='accounts/login_form.html', already_logged_url=None, 
                       redirect_to=None):
    #### ARGS ####
    #template = O template onde o form será renderizado.
    #already_logged_url = URL que indica para onde o usuário será redirecionado caso já esteja logado.
    #redirect_to = URL para onde o usuário irá depois do login

    #Se o usuário já estiver autenticado e forçar a url de login, o enviamos 
    #para a url setada em already_logged_url, caso não informada envia o usuário para a home. 
    if request.user.is_authenticated():
		return HttpResponseRedirect(already_logged_url or '/')

        
    #Primeiro verifica se há um redirect_to como argumento da view, caso não encontre ele tenta
    #usar o LOGIN_REDIRECT do settings, se também não tiver sucesso ele redirecionará o usuário
    #para a home (tudo isso após o login).
    if redirect_to:
        to = redirect_to
    else:
        to = getattr(settings, 'LOGIN_REDIRECT', '/')

 
    if request.method == 'POST':
        form = LoginForm(request.POST)

        #O método u_login se encarrega de verificar se o form é valido e retorna sempre um boleano,
        #caso seja True ele já faz o login do usuário e o redireciona para a página seguinte.
        if form.u_login(request):            
            return HttpResponseRedirect(to)

    else:
        form = LoginForm()

    #Faz a renderização do formulário passando uma variável 'form' para o contexto
    response = simple.direct_to_template(request,
                                         template = template,
                                         extra_context = {'form': form})
    return response      
    
