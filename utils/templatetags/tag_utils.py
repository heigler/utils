# -*- coding: utf-8 -*-

from django import template
from django.conf import settings

register = template.Library()


def do_evalto(parser, token):
    nodelist = parser.parse(('endevalto',))
    parser.delete_first_token()
    return EvalToNode(nodelist, token.split_contents()[1])

class EvalToNode(template.Node):
    """
    Return a evaluated value and set a variable with its results
    exemplo:
    {% evalto "special_css" %}style/section/{{ request.site_info.slug }}/base.css{% endevalto %}
    """
    
    def __init__(self, nodelist, var_name):
        self.nodelist = nodelist
        self.var_name = template.Variable(var_name)
    
    def render(self, context):
        context[self.var_name.resolve(context)] = self.nodelist.render(context)
        return ''
    
register.tag('evalto', do_evalto)

# Filters from: http://www.djangosnippets.org/snippets/465/

@register.filter
def multiple_of(value,arg):
    return value % arg == 0

@register.filter
def in_list(value,arg):
    return value in arg

@register.filter
def is_equal(value,arg):
    return value == arg

@register.filter
def is_not_equal(value,arg):
    return value != arg

@register.filter
def is_lt(value,arg):
    return int(value) < int(arg)

@register.filter
def is_lte(value,arg):
    return int(value) <= int(arg)

@register.filter
def is_gt(value,arg):
    return int(value) > int(arg)

@register.filter
def is_gte(value,arg):
    return int(value) >= int(arg)
