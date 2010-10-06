# -*- coding: utf-8 -*-

from django.core.mail import EmailMultiAlternatives, send_mail, SMTPConnection
from django.template import loader, Context
from django.conf import settings


def create_message(sender,to,subject,text_body,html_body,connection,headers):
    """
    Função genérica para envio de e-mail multipart
    """
    # Cria uma mensagem multipart
    msg = EmailMultiAlternatives(
        # Prefixa o assunto de acordo com as configurações
        settings.EMAIL_SUBJECT_PREFIX + subject,
        # Corpo da mensagem em formato texto
        text_body,
        # Remetente
        sender,
        # Destinatário(s)
        to,
        # Conexão SMTP
        connection=connection,
        # Headers especiais
        headers=headers
    )
    
    # Acrescenta a parte HTML
    msg.attach_alternative(html_body, 'text/html')
    
    return msg
        

def send_html_mail(to, tmpl_basename, context = {}, subject = '', sender=settings.DEFAULT_FROM_EMAIL, reply_to=None):
    """
    Envia um e-mail multipart HTML + texto com base em templates. 
    """
    
    # Converte o destinatário para uma lista se não for uma lista ou tupla
    if not isinstance(to, (tuple, list)):
        to = [to]
    
    # Junta parâmetros de envio com o contexto do template
    # * Prioriza o contexto definido pelo usuário,
    # * permitindo sobrescrever o 'to' e 'subject'
    mail_context = Context({'to': ', '.join(to), 'subject': subject})
    mail_context.update(context)
    
    # Renderiza os templates, texto e html
    text_body = loader.render_to_string(tmpl_basename + '.txt', mail_context)
    html_body = loader.render_to_string(tmpl_basename + '.html', mail_context)
    
    # Cria uma conexão SMTP, 
    connection = SMTPConnection(username=None, password=None, fail_silently=False)
    
    # Cria headers para resposta
    headers = reply_to and {'Reply-to': reply_to, 'From': reply_to} or {}
    
    msg = create_message(sender, to, subject, text_body, html_body, connection, headers)
    
    # Envia a mensagem
    msg.send()
