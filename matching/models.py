from django.db import models

# Create your models here.
class CustomUser(models.Model):
    phone = models.TextField(max_length=20, blank=False)
    first_name = models.CharField(max_length=130, blank=True)
    last_name = models.CharField(max_length=130, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.first_name:
            return self.first_name + " " + self.last_name
        else:
            return self.phone
    
