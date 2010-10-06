from django import template

register = template.Library()


@register.inclusion_tag('fo_default.html')
def build_form(form):
    context = {'form': form}
    
    return context