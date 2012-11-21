from django.db import models


class URLQueue(models.Model):
    
    status = models.IntegerField(default=0)
    
    number = models.IntegerField()
    title = models.CharField(max_length=255)

    singer = models.CharField(max_length=255)
    album = models.CharField(max_length=255)
    artist = models.CharField(max_length=255) 

    pub = models.DateField()
    company = models.CharField(max_length=255)

    is_del = models.IntegerField(default=0)
    create = models.DateTimeField(auto_now_add=True)
    start = models.DateTimeField(null=True)
    duration = models.IntegerField(null=True)
    age = models.IntegerField(default=0, db_index=True)

    url = models.TextField()
    url_hash = models.CharField(max_length=255, unique=True)

    path = models.TextField(null=True) 


class Gotcha(models.Model):
    
    number = models.IntegerField()
    title = models.CharField(max_length=255)

    singer = models.CharField(max_length=255)
    album = models.CharField(max_length=255)

    pub = models.DateField()
    company = models.CharField(max_length=255)

    url = models.TextField()
    url_hash = models.CharField(max_length=255, unique=True)
    
    path = models.TextField(null=True) 

    start = models.DateTimeField(null=True)
    duration = models.IntegerField(null=True)
    status = models.IntegerField(default=0, db_index=True)