# -*- coding: utf-8 -*-
import sys
import urllib2, urllib
from django.http import HttpResponse
#DJANGO
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe


class AutoImageWidget(forms.FileInput):
    """
    A FileField Widget that shows its current value if it has one.
    """
    def __init__(self, attrs={}):
        super(AutoImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('<img src="%s" alt="" /><br /><small>%s</small>' % (value.url, _('Mudar a foto')))              
        output.append(super(AutoImageWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))

