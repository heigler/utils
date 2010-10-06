#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import sys
import urllib

MODPATH = os.path.abspath(os.path.dirname(__file__))

project_name = raw_input('Nome do projeto:\n')



os.system('django-admin.py startproject %s' % project_name)


sys.path.insert(0, os.path.join(MODPATH, project_name))


#Pega a SECRET_KEY gerada pelo django
from settings import SECRET_KEY


settings_config = '''import os

TIME_ZONE = 'America/Sao_Paulo'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

MODPATH = os.path.abspath(os.path.dirname(__file__))
abs = lambda path: os.path.join(MODPATH, path)

MEDIA_ROOT = abs('media')

MEDIA_URL = '/media/'

ADMIN_MEDIA_PREFIX = '/media/admin/'

SECRET_KEY = '%(key)s'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = '%(project)s.urls'

TEMPLATE_CONTEXT_PROCESSORS = ('django.core.context_processors.auth',
                                'django.core.context_processors.debug',
                                'django.core.context_processors.media',
                                'django.core.context_processors.request',
                                )

TEMPLATE_DIRS = (
                 abs('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'utils',
    'utils.formoptions',
    #'utils.generic_accounts',
)

from local_settings import *

''' %({'key': SECRET_KEY, 'project': project_name})


settings_file = open('%s/settings.py' %project_name, 'w+')
settings_file.write(settings_config)
settings_file.close()

os.system('touch %s/local_settings.py' %project_name)

local_settings_config = '''DEBUG = True
TEMPLATE_DEBUG = DEBUG

#EMAIL
DEFAULT_FROM_EMAIL = '' #eg 'lordheigler@gmail.com'
EMAIL_HOST = '' #eg smtp.gmail.com
EMAIL_HOST_USER = '' #eg 'lordheigler@gmail.com'
EMAIL_HOST_PASSWORD = '' #eg 3612pitukaoxlcjf
EMAIL_PORT = 587
EMAIL_SUBJECT_PREFIX = u'' #eg Herz Metal
EMAIL_USE_TLS = True
#END EMAIL


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = ''
DATABASE_USER = 'root'
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

'''

local_settings_file = open('%s/local_settings.py' %project_name, 'w+')
local_settings_file.write(local_settings_config)
local_settings_file.close()


manage_config = '''#!/usr/bin/env python
import os
import sys

MODPATH = os.path.abspath(os.path.dirname(__file__))
sys.path += [os.path.join(MODPATH, '..', 'apps'),]

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r." % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)

'''

manage_file = open('%s/manage.py' %project_name, 'w+')
manage_file.write(manage_config)
manage_file.close()


urls_config = '''from django.conf.urls.defaults import url, patterns, include
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),

    #Test view
    (r'^$', direct_to_template, {'template': 'base.html'}),
    
    #accounts
    #(r'^accounts/', include('utils.generic_accounts.urls')),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

'''

urls_file = open('%s/urls.py' %project_name, 'w+')
urls_file.write(urls_config)
urls_file.close()


os.chdir('%s' %project_name)
os.system('mkdir templates')
os.system('touch templates/404.html templates/500.html templates/base.html')
os.system('mkdir -p media/js media/style media/libs')
os.system('touch media/style/base.css media/style/forms.css media/js/base.js')


basehtml_config = '''{% load html %}
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
	<title>{% block title %}{% endblock %}</title>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta name="keywords" content="{% block extra_keywords %}{% endblock %}" />

	<!-- CSS -->
	{% html_media 'style/base.css' %}
	{% block css %}{% endblock %}
	<!-- END OF CSS -->

	<!-- JS -->
	{% html_media 'js/j.js' %}
	{% html_media 'js/base.js' %}
	{% block js %}{% endblock %}
	<!-- END OF JS -->

</head>

<body>
	<div id="container">
		
		<!-- HEADER -->
		<div id="header">
		</div>
		<!-- END OF HEADER -->
		
		<!-- PAGE -->
		<div id="page">
		{% block inner_page %}{% endblock %}			
		</div>
		<!-- END OF PAGE -->

		<!-- FOOTER -->
		<div id="footer">		
		</div>	
		<!-- END OF FOOTER -->
		
	</div>
</body>
</html>
'''

basehtml = open('templates/base.html', 'w+')
basehtml.write(basehtml_config)
basehtml.close()


basecss_config = '''*{
	margin: 0;
	padding: 0;
}

body{
	font-family: Arial;
	background: #ccc;
}

#container{
	width: 1000px;
	margin: 0 auto;
	text-align: center;
}

	#container #header,
		      #page,
		      #footer{
		clear: both;
		width: 960px;
		float: left;
		text-align: left;
		padding: 10px 20px;
	}

	/* HEADER */
	#container #header{
		background: #C5DFC0;
	}
	/* END OF HEADER */
	
	/* PAGE */
	#container #page{
		background: #BFB6B1;
	}
	/* END OF PAGE */

	/* FOOTER */
	#container #footer{
		background: #CFACC6;
	}
	/* END OF FOOTER */


/* WARNINGS */
p.warning{

}
	p.warning .success{

	}
	p.warning .alert{

	}
	p.warning .fail{

	}
/* END OF WARNINGS */
'''

basecss_file = open('media/style/base.css', 'w+')
basecss_file.write(basecss_config)
basecss_file.close()


basejs_config = '''$(function(){
	
	alert('Javascript with jquery lib is working');

});
'''

basejs_file = open('media/js/base.js', 'w+')
basejs_file.write(basejs_config)
basejs_file.close()

print '===> baixando jquery'
urllib.urlretrieve('http://jqueryjs.googlecode.com/files/jquery-1.3.2.min.js', 'media/js/j.js')
print '===> baixando plugin jquery mask'
urllib.urlretrieve('http://jquery-joshbush.googlecode.com/files/jquery.maskedinput-1.2.2.min.js', 'media/js/j.mask.js')
#print '===> baixando tiny mce'
#urllib.urlretrieve('http://sourceforge.net/projects/tinymce/files/TinyMCE/3.2.6/tinymce_3_2_6.zip/download', 'media/libs/tinymce.zip')
#os.chdir('media/libs')
#os.system('unzip tinymce.zip > /dev/null')
#os.system('mv -f tinymce/jscripts/tiny_mce tiny_mce')
#os.system('rm -rf tinymce.zip tinymce')

os.system('rm *pyc')

print 'Projeto %s criado com sucesso.' %project_name
