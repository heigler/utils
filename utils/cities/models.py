# -*- coding: utf-8 -*-

from django.db import models

class Country(models.Model):
    acronym = models.CharField(max_length=2)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'countries'
        
    def __unicode__(self):
        return self.name
    
class State(models.Model):
    country = models.ForeignKey(Country)
    acronym = models.CharField(max_length=2)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ('name',)
        
    def __unicode__(self):
        return self.name


class City(models.Model):
    state = models.ForeignKey(State)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'cities'

    def __unicode__(self):
        return self.name

class District(models.Model):
    city = models.ForeignKey(City)
    name = models.CharField(max_length=50)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return u'%s' % self.name

class Region(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    state = models.ForeignKey(State)
    cities = models.ManyToManyField(City)
    
    class Meta:
        ordering = ('name',)
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.state.acronym)
