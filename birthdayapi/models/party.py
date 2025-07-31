from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Party(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=300)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_parties')
    
    # Social features
    facebook_live_url = models.URLField(blank=True, null=True)
    venmo_username = models.CharField(max_length=100, blank=True)
    
    # Location coordinates for map
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Party settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    max_guests = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Parties"
        ordering = ['-date']
    
    def __str__(self):
        return self.name
    
    @property
    def is_past(self):
        return timezone.now() > self.date
    
    @property
    def total_rsvps(self):
        return self.rsvps.count()
    
    @property
    def attending_count(self):
        return self.rsvps.filter(status='yes').count()
