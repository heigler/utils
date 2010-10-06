# -*- coding: utf-8 -*-

from django import template
from django.conf import settings
from django.shortcuts import render_to_response

from quick_tag import quick_tag

register = template.Library()

def positive(i):
    return i < 0 and i*-1 or i

@register.inclusion_tag('main/includes/paginate.html', takes_context=True)
def paginate(context,paginator,current_page,url,adjacent=5):
    display_page_limit = adjacent*2
    current = current_page.number
    page_min = max(0, current - adjacent)
    # devolve a página máxima e caso for a primeira, devolve também a diferença para manter sempre o número total de páginas páginas
    # TODO: corrigir primeira e segunda página
    max_current = current > adjacent and current-adjacent or adjacent-current
    max_valid = current in range(adjacent) and current+max_current*2 or current + adjacent
    
    page_max = min(paginator.num_pages, max_valid)
    diff = page_max-page_min

    #mantém o número de páginas mesmo quando está nas últimas páginas
    if ((page_min > 0) and
        (diff < display_page_limit)):
        page_min = max(0, page_min-(display_page_limit-diff))
    
    page_range = paginator.page_range[page_min:page_max]
    
    c = {'paginator': paginator,
         'current_page': current_page,
         'page_url': url,
         'page_range': page_range,
         }
    
    return c