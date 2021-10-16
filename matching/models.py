from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class CustomUser(models.Model):
    phone = models.TextField(max_length=20, blank=False)
    first_name = models.CharField(max_length=130, blank=True)
    last_name = models.CharField(max_length=130, blank=True)
    fun_fact = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    num_matches_found = models.IntegerField(default=0, blank=True)
    match_ids = ArrayField(models.IntegerField(blank=True), default=list)
    # Time (unix) at which matches were found, if any.
    match_create_times = ArrayField(models.IntegerField(), default=list)
    match_found_times = ArrayField(models.IntegerField(), default=list)
    num_matched_to_me = models.IntegerField(default=0, blank=True)

    def __str__(self):
        if self.first_name:
            return self.first_name + " " + self.last_name
        else:
            return self.phone
    
    def to_json(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'fun_fact': self.fun_fact,
        }
