# -*- coding: utf-8 -*-

import os
import time

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe, SafeUnicode
from django.db.models.fields.files import ImageFieldFile
from django import forms

from quick_tag import quick_tag
from utils import fs, imaging


register = template.Library()

## HELPERS

def url_to_root(path):
    """
    Recebe uma URL local e retorna o caminho no sistema de arquivos.
    """

    # Verifica se foi passado um caminho

    if not path:
        return path

    # Remove a MEDIA_URL do início do caminho
    if path.startswith(settings.MEDIA_URL):
        path = path.replace(settings.MEDIA_URL, '', 1)

    # Prefixa o caminho com o caminho local para os arquivos estáticos
    newpath = os.path.join(settings.MEDIA_ROOT, path)
    return newpath

def nocache(path):
    """
    Recebe o caminho de um arquivo.
    Retorna um string baseado na data de modificação do arquivo.

    Útil para evitar o cache de arquivos estáticos por parte do browser.
    """

    # Verifica se foi passado um caminho
    if not path:
        return ''

    # Converte a URL em caminho para o sistema de arquivos
    full_path = url_to_root(path)

    # Verifica se o arquivo existe
    if os.path.isfile(full_path):
        # Lê a data de modificação do arquivo
        m_time = time.localtime(os.path.getmtime(full_path))
        # Retorna a data no formato "modified=[dia_ano][hora][minuto][segundo]"
        return time.strftime('modified=%j-%H%M%S', m_time)

    return ''

## TAGS

def html_image(context, src, width = None, height = None, method='crop', quality=80, **kwargs):
    """
    Função para lidar com imagens.
    Faz o redimensionamento automático de imagens locais. 
    """
    
    # Precisa ter um caminho local
    if not (src and src.startswith('/')):
        return kwargs
    
    # Remove a URL base de media
    clean_path = src.replace(settings.MEDIA_URL, '', 1)
    # Caminho físico do arquivo
    path = os.path.join(settings.MEDIA_ROOT, clean_path)
    
    img = None
    
    # Só processar o arquivo se alguma dimensão foi passada
    if width or height:
        
        # Marca o nome de arquivo de acordo com o método (crop ou fit)
        extra = ((method == 'crop') and '_c_') or '_t_'
        
        # Parâmetros para a função de redimensionamento
        kw = {}

        if width:
            extra += 'w' + width
            kw['max_width'] = width
        if height:
            extra += 'h' + height
            kw['max_height'] = height

        # Cria o nome da imagem redimensionada:
            # 100x50 crop em "1.jpg": 1_c_w100h50.jpg
            # 200x120 fit em "2.jpg": 2_t_w200h120.jpg
            # 100 width fit em "3.jpg": 3_c_w200.jpg
        clean_path = fs.add_to_basename(clean_path, extra)
    
        # Separa nome base e extensão
        basepath, ext = os.path.splitext(clean_path)
        # Extensão em minúsculas
        ext = ext.lower()
        
        # Converte BMPs para PNGs, para economizar espaço e banda
        if ext == '.bmp':
            clean_path = basepath + '.png'
            
        # Caminho completo para o novo arquivo
        kw['save_as'] = os.path.join(settings.MEDIA_ROOT, clean_path)
    
        # Só processa o arquivo se não existir
        # ou se o destino é mais antigo do que o original 
        if not os.path.isfile(kw['save_as']) or (os.path.getmtime(path) >= os.path.getmtime(kw['save_as'])):
            # Redimensiona e guarda o objeto
            img = imaging.resize_file(path, quality=quality, method=method, **kw)
        # Caso contrário, apenas carrega a imagem  
        else:
            img = imaging.image_open(kw['save_as'])
    
        context['src'] = '/'.join((settings.MEDIA_URL, clean_path)).replace('//', '/')
        
    # Nenhum processamento feito?
    else:
        # Carrega a imagem
        img = imaging.image_open(path)
    
    # Atualiza dimensões da imagem no contexto
    context['width'], context['height'] = img.size
    
    return kwargs

def html_flash(context, src, **kwargs):
    context['wmode'] = kwargs.pop('wmode', 'opaque')
    return kwargs

# Funções customizadas para cada extensão
custom_html_media = {
    'bmp': html_image,
    'gif': html_image,
    'jpeg': html_image,
    'jpg': html_image,
    'png': html_image,
    'swf': html_flash,
}

@register.tag
@quick_tag
def html_media(context, src, get = '', **kwargs):
    """
    Tag para centralizar como é feita a exibição de elementos html.
    Cada elemento é renderizado com um template de acordo com a extensão do objeto.

    Exemplo de uso:
    {% load html %}
    {% html_media 'pic.jpg' width=50 height=100 %}
    """
    
    # Falha silenciosamente se não houver um caminho
    if not src:
        return ''

    #se o src for um ImageFieldFile
    if isinstance(src,ImageFieldFile):
        src = src.name

    # Se o caminho não for externo ou absoluto, prefixa com o `MEDIA_URL`
    
    if not src.startswith('http'):
        if not src.startswith('/'):
            src = settings.MEDIA_URL + src
            
        # Falha silenciosamente se o arquivo local não existir
        if not os.path.isfile(url_to_root(src)):
            return ''
            
        # Acrescenta a data de modificação ao query-string
        get += (get and '&' or '') + nocache(src)

    # Adiciona '?' se houver um query-string
    get = (get and '?' or '') + get
    
    # Quebra o caminho e a extensão
    try:
        src_no_ext, ext = src.rsplit('.', 1)
    except ValueError:
        src_no_ext = src
        ext = ''
    
    # Contexto para o objeto a ser renderizado
    object_context = kwargs.copy()
    object_context.update({
        'src': src,
        'ext': ext,
        # Acrescenta o caminho sem extensão
        # para o script de ativação de activex para o IE
        'src_no_ext': src_no_ext,
        'get': get,
    })
    
    # Argumentos adicionais serão convertidos em atributos HTML
    attrs = kwargs
    
    # Get a custom function by extension
    custom = custom_html_media.get(ext)
    if custom:
        try:
            # Executa a função específica e permite que altere os atributos
            attrs = custom(object_context, src, **kwargs) or {}
        except:
            pass
        
    str_attrs = ''
    if attrs.has_key('attrs'):
        str_attrs = attrs['attrs']
        del attrs['attrs']
    
    str_attrs += ' ' + ' '.join(['%s="%s"' % i for i in attrs.items()])
    
    object_context['attrs'] = mark_safe(str_attrs)
    
    return template.loader.render_to_string('utils/html/%s.html' % ext.lower(), object_context)

@register.tag
@quick_tag
def html_image_resize(context, src, **kwargs):
    """
    Função redimensionar imagens.
    Faz o redimensionamento automático de imagens locais. 
    """
    
    if not ((src and src.startswith('/')) or (width or height)):
        return src
    
    html_image(context, src, **kwargs)
    
    return context['src']

@register.tag
@quick_tag
def html_form_field(context, f, type='field', **kwargs):
    
    field = f.field
    
    for att, value in kwargs.items():
        field.widget.attrs[att] = value
    
    object_context = {'field': f}
    
    return template.loader.render_to_string(('utils/html_forms/%s.html' % type,
                                             'utils/html_forms/field.html'), object_context)

# FILTERS

@register.filter
def number_format(num, places=0):
    """Format a number according to locality and given places"""
    import locale
    locale.setlocale(locale.LC_ALL, "")
    return locale.format("%.*f", (places, num), True)


@register.filter
def remove_tag_blocks(text,taglist):
    """ Remove um bloco inteiro das tags na lista separada por espaço, ex: 
    texto|remove_tag_block:"table"
    <table class="table"><tr><td>Este texto será removido</td></tr></table>
    """
    tags = taglist.split()
    new = text
    for tag in tags:
        #cuidado, a tag de abertura não pode ter o ">" senão pode entrar em loop infinito caso não encontre 
        open = '<%s' % tag 
        close = '</%s>' % tag
        # TODO: Retirar todos os blocos que aparecerem
        #while new.find(open)>0:
        inipos = new.find(open)
        endpos = new.find(close)+len(close)
        new = new[:inipos]+new[endpos:]
    return new
