from django.contrib.auth.models import User
from django.db import models
class Preliminary(models.Model):
        user = models.ForeignKey(User, blank=True, null=True)
	slug = models.CharField(max_length=255)
        save_string  = models.TextField()
