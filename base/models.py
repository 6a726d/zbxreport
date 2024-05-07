from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class TBHostGroup(models.Model):
    gpzbxid = models.IntegerField()
    gpname = models.CharField(max_length = 50)
    gpusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbhostgroup'
    
class TBHost(models.Model):
    hostzbxid = models.IntegerField()
    hostname = models.CharField(max_length = 50)
    hostusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbhost'

class TBMiddleHost(models.Model):
    mdhhostid = models.ForeignKey(TBHost, on_delete = models.CASCADE)
    mdhhostgpid = models.ForeignKey(TBHostGroup, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbmiddlehost'

class TBItens(models.Model):
    itemname = models.CharField(max_length = 400)
    itemdscreport = models.CharField(max_length = 400, null = True, blank = True)
    itemusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbitens'

class TBMiddleItem(models.Model):
    mdiitemid = models.IntegerField()
    mdiitemname =  models.ForeignKey(TBItens, on_delete = models.CASCADE)
    mdihostid = models.ForeignKey(TBHost, on_delete = models.CASCADE)
    mdiusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbmiddleitem'

class TBAPI(models.Model):
    apiurl = models.CharField(max_length = 100)
    apiusr = models.CharField(max_length = 50)
    apipass = models.CharField(max_length=100)
    apitoken = models.CharField(max_length=100)
    apiusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbapi'

class TBLayout(models.Model):
    layoutname = models.CharField(max_length = 100)
    layoutemp = models.CharField(max_length = 100)
    layoutlogo = models.FileField(upload_to = 'logo', null = True, blank = True)
    layoutdsc = models.CharField(max_length = 500)
    layoutusrid = models.ForeignKey(User, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tblayout'

class TBMiddleLayout(models.Model):
    mdlid = models.ForeignKey(TBLayout, on_delete = models.CASCADE)
    mdlitemname = models.ForeignKey(TBItens, on_delete = models.CASCADE)

    class Meta:
        db_table = 'tbmiddlelayout'