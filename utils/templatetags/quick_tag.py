# -*- coding: utf-8 -*-

from django import template
import re

register = template.Library()

# Expressão regular para encontrar argumentos nomeados
# Começando com qualquer [não(igual,aspas,aspas-simples)] seguido de um igual
re_kw = re.compile('^([^="\']+)=(.+)')

class QuickTagNode(template.Node):
    """
    Node genérico que faz a resolução automática das variáveis / parâmetros
    e executa uma função de renderização customizada.

    A função recebe sempre o contexto como primeiro parâmetro e em seguida
    os outros parâmetros. Deve retornar um string a ser renderizado.

    Suporta parâmetros nomeados.

    Exemplo:
        ``
        @register.tag
        @quick_tag
        def quick_example(context, *args, **kwargs):
            return ''
        ``

    Uso no template:
        ``
        {% quick_example 'quick' kw_param="example" %}
        ``
    """

    def __init__(self, func, vars_to_resolve):
        # Função de renderização
        self.func = func
        # Argumentos para a função
        self.args = []
        self.kwargs = {}

        # Passa pelas variáveis a serem resolvidas (baseado na `simple_tag` do Django)
        for var in vars_to_resolve:
            # Testa para descobrir se é um argumento nomeado
            m = re_kw.match(var)
            if m:
                # Adiciona a variável ao dicionário de argumentos
                self.kwargs[m.group(1)] = template.Variable(m.group(2))
            else:
                # Adiciona a variável à lista de argumentos
                self.args.append(template.Variable(var))

    def render(self, context):
        # Resolução de variáveis (baseado na `simple_tag` do Django)
        # Argumentos
        args = [v.resolve(context) for v in self.args]
        # Argumentos nomeados
        kwargs = dict([(str(k), v.resolve(context)) for k,v in self.kwargs.iteritems()])

        return self.func(context, *args, **kwargs)

def quick_tag(func):
    def _dec(parser, token):
        return QuickTagNode(func, token.split_contents()[1:])
    # Copia metadados para a função decorada
    _dec.__name__ = func.__name__
    _dec.__doc__ = func.__doc__
    _dec.__dict__.update(func.__dict__)
    return _dec
