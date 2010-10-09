# -*- coding: utf-8 -*-

from django import forms
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.localflavor.br.forms import EMPTY_VALUES, DV_maker
from django.dispatch import dispatcher
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import UploadedFile, SimpleUploadedFile
from django.utils.encoding import smart_str

import re, os, glob, sys, shutil
from cStringIO import StringIO

from imaging import resize
from fs import *

def auto_upload_to(instance, cls, name):
    """
    Set 'upload_to' based on the format: app_name/model_name/field_name
    """
    instance.upload_to = '/'.join([cls._meta.app_label, cls.__name__, name]).lower()

def auto_save_form_data(self, instance, data):

    ###### todo - criar um signal para renomear o arquivo com o ID
    
    # Make sure we have an ID
    if not instance.pk:
        instance.validate()
        instance.save()

    # Split basename and extension
    original, ext = os.path.splitext(data.name)

    # Set the name: pk.ext
    data.name = change_basename(data.name, str(instance.pk))
    
    # Remove the file if already exists
    path = os.path.join(settings.MEDIA_ROOT, self.upload_to, data.name)
    if os.path.exists(path):
        os.remove(path)

def auto_rename(file_path, new_name):
    """
    Renames a file, keeping the extension.
    
    Parameters:
        - file_path: the file path relative to MEDIA_ROOT
        - new_name: the new basename of the file (no extension)
    
    Returns the new file path on success or the original file_path on error.
    """
    
    # Return if no file given
    if not file_path:
        return ''
    else:
        file_path = file_path
    
    # Get the new name
    new_path = change_basename(file_path, new_name)
    
    
    # Changed?
    if new_path != file_path:
        # Try to rename
        try:
            shutil.move(os.path.join(settings.MEDIA_ROOT, file_path), os.path.join(settings.MEDIA_ROOT, new_path))
        except IOError:
            # Error? Restore original name
            new_path = file_path
    
    # Return the new path replacing backslashes (for Windows)
    return new_path
        
class AutoFileField(models.FileField):

    def __init__(self, verbose_name=None, name=None, **kwargs):
        
        # Flag to indicate when the file should be renamed
        self.rename = False
        
        super(AutoFileField, self).__init__(verbose_name, name, **kwargs)
    
    def contribute_to_class(self, cls, name,**kwargs):
        super(AutoFileField, self).contribute_to_class(cls, name,**kwargs)
        # Auto-adjust 'upload_to' path
        auto_upload_to(self, cls, name)
        # Connect the post-save signal of the model with the file renaming method
        signals.post_save.connect(self._post_save,sender=cls)

    
    def _post_save(self, instance=None,**kwargs):
        # Make sure there's an instance and the file must be renamed
        if not instance or not self.rename:
            return
        # Change the filename based on the instance primary key
        filename = auto_rename(getattr(instance, self.attname).name, '%s' % instance.pk)
        contents = open(os.path.join(settings.MEDIA_ROOT, filename))
        
        setattr(instance, self.attname, filename)
        # Remove the renaming flag
        self.rename = False
        # Save the instance      
        instance.save()
        #instance.save(filename,contents,save=False)
        
    def get_filename(self, filename):
        # Somehow slashes were replaced by backslashes, causing URLs to fail, fixing here
        return super(AutoFileField, self).get_filename(filename).replace('\\', '/')

    def save_form_data(self, instance, data):
        # Make sure there's an upload
        if not data or not isinstance(data, UploadedFile):
            return
        
        self.rename = True
        super(AutoFileField, self).save_form_data(instance, data)

    def get_internal_type(self):
        return 'FileField'

class AutoImageField(models.ImageField):

    def __init__(self, verbose_name=None, name=None, width=None, height=None, method='crop', quality=80, **kwargs):
        
        self.width = width
        self.height = height
        self.method = method
        self.quality = quality
        
        # Flag to indicate when the file should be renamed
        self.rename = False
        
        super(AutoImageField, self).__init__(verbose_name, name, **kwargs)
    
    def contribute_to_class(self, cls, name, **kwargs):
        super(AutoImageField, self).contribute_to_class(cls, name, **kwargs)
        # Auto-adjust 'upload_to' path
        auto_upload_to(self, cls, name, **kwargs)
        # Connect the post-save signal of the model with the file renaming method
        signals.post_save.connect(self._post_save,sender=cls)
    
    def _post_save(self, instance=None, **kwargs):
        # Make sure there's an instance and the file must be renamed
        if not instance or not self.rename:
            return
        # Change the filename based on the instance primary key
        filename = auto_rename(getattr(instance, self.attname).name, '%s' % instance.pk)
        setattr(instance, self.attname, filename)
        # Remove the renaming flag
        self.rename = False
        # Save the instance
        instance.save()

    def get_filename(self, filename):
        # Somehow slashes were replaced by backslashes, causing URLs to fail, fixing here
        return super(AutoImageField, self).get_filename(filename).replace('\\', '/')

    def save_form_data(self, instance, data):
        
        # Make sure there's an upload
        if not data or not isinstance(data, UploadedFile):
            return
        
        # Create a string stream from the uploaded file and resize
        data.seek(0)
        img = resize(
            StringIO(data.read()),
            max_width=self.width, max_height=self.height,
            method=self.method
        )
        # Extract the basename and extension
        basename, ext = os.path.splitext(data.name)
        # Remove the '.'
        ext = ext[1:]
        
        # Set the image format based on the extension
        format = ext.upper()
        
        # Fix format name for extension .JPG
        if format == 'JPG':
            format = 'JPEG'
        # Convert BMPs to PNG to save space and bandwidth
        elif format == 'BMP':
            format = 'PNG'
            data.filename = basename + '.png'
        # Use a stream to optimize and set the quality (don't use 'optimize' for GIF files)
        out_file = StringIO()
        img.save(out_file, format=format, quality=self.quality, optimize=(format != 'GIF'))
        out_file.reset()
        
        # Put the resized image back to the content
        data = SimpleUploadedFile(data.name, out_file.read(), data.content_type)

        # auto_save_form_data(self, instance, data)
        self.rename = True
        super(self.__class__, self).save_form_data(instance, data)

    def delete_file(self, instance, sender, **kwargs):
        """
        Deletes left-overs from thumbnail or crop template filters.
        """
        super(AutoImageField, self).delete_file(instance, sender)
        if getattr(instance, self.attname):
            # Get full path and the base directory that contains the file
            file_name = getattr(instance,self.name).name
            basedir = os.path.dirname(file_name)
            
            # Look for thumbnails created from filters for the current filename
            # and delete the files
            mask = add_to_basename(file_name, '_*')
            [os.remove(os.path.join(basedir, f)) for f in glob.glob(mask)]



rules = [
  (
    (AutoImageField, AutoFileField),
    [],
    {},
  )
]
from south.modelsinspector import add_introspection_rules
add_introspection_rules(rules, ["^utils"])


BR_DATE_INPUT_FORMATS = (
    '%d/%m/%y', # 15/02/80
    '%d/%m/%Y', # 15/02/1980
)

class BRDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        super(BRDateField, self).__init__(input_formats=BR_DATE_INPUT_FORMATS, *args, **kwargs)


def make_int(value):
    if value:
        #formata para padrão americano
        value = value.replace('.','')
        value = value.replace(',','.')
        #converte em float para prevenir erros de nºs com ponto
        value = int(float(value))
    else:
        value = 0
    return value        
        
class PlainIntegerField(forms.CharField):
    """
    Transforma um valor float em inteiro
    """
    def clean(self,value):
        if value:
            return make_int(value)
        else:
            return ''

class CommaWidget(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if value:
            value = smart_str(value).replace(',', '.')
            value = '%.2f' % float(value)
            value = value.replace('.', ',')
        return super(CommaWidget, self).render(name, value)

class CommaDecimalField(forms.DecimalField):
    """
    Extension to DecimalField that allows comma-separated Decimals to be entered and displayed
    """
    widget = CommaWidget
    
    def __init__(self, *args, **kwargs):
        if kwargs.has_key('initial'):
            print kwargs['initial']
            kwargs['initial'] = kwargs['initial'].replace(',', '.')
        super(CommaDecimalField, self).__init__(*args, **kwargs)
    
    def clean(self, value):
        value = smart_str(value).replace(',', '.')
        return super(CommaDecimalField, self).clean(value)

class BRCPFCNPJField(forms.CharField):
    
    default_error_messages = {
        'invalid': u"CPF/CNPJ Inválido.",
        'max_digits': u"Este campo permite de 11 a 19 caracteres.",
        'digits_only': u"Digite apenas números e separadores",
    }

    def __init__(self, *args, **kwargs):
        kwargs.pop('max_length', None)
        kwargs.pop('min_length', None)
        super(BRCPFCNPJField, self).__init__(max_length=19, min_length=11, *args, **kwargs)

    def clean(self, value):
        
        value = super(BRCPFCNPJField, self).clean(value)
        
        if value in EMPTY_VALUES:
            return u''
        orig_value = value[:]
        if not value.isdigit():
            value = re.sub("[-\./]", "", value)
        try:
            int(value)
        except ValueError:
            raise forms.ValidationError(self.error_messages['digits_only'])
        
        length = len(value)
        if length not in (11, 14):
            raise forms.ValidationError(self.error_messages['max_digits'])
        
        orig_dv = value[-2:]
        
        # Valida como CPF se tiver 11 dígitos
        if length == 11:
    
            new_1dv = sum([i * int(value[idx]) for idx, i in enumerate(range(10, 1, -1))])
            new_1dv = DV_maker(new_1dv % 11)
            value = value[:-2] + str(new_1dv) + value[-1]
            new_2dv = sum([i * int(value[idx]) for idx, i in enumerate(range(11, 1, -1))])
            new_2dv = DV_maker(new_2dv % 11)
            value = value[:-1] + str(new_2dv)
        
        # Valida como CNPJ se tiver 14 dígitos
        elif length == 14:
            new_1dv = sum([i * int(value[idx]) for idx, i in enumerate(range(5, 1, -1) + range(9, 1, -1))])
            new_1dv = DV_maker(new_1dv % 11)
            value = value[:-2] + str(new_1dv) + value[-1]
            new_2dv = sum([i * int(value[idx]) for idx, i in enumerate(range(6, 1, -1) + range(9, 1, -1))])
            new_2dv = DV_maker(new_2dv % 11)
            value = value[:-1] + str(new_2dv)
        
        if value[-2:] != orig_dv:
            raise forms.ValidationError(self.error_messages['invalid'])

        return orig_value
