from django.db import models

class scheduletable(models.Model):
    userID = models.TextField()
    caltype = models.CharField(max_length=6)
    groupID = models.TextField()
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=2)
    day = models.CharField(max_length=2)
    hour = models.CharField(max_length=2)
    minute = models.CharField(max_length=2)
    content = models.TextField()

class usertable(models.Model):
    userID = models.TextField()
    caltype = models.CharField(max_length=6)
    password = models.TextField()
    groupID = models.TextField()
    authrank = models.CharField(max_length=2)
    grouppassword = models.TextField()

    def __str__(self):
        return self.password