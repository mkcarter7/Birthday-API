from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class RSVP(models.Model):
    STATUS_CHOICES = [
        ('yes', 'Yes, I\'ll be there!'),
        ('no', 'Sorry, can\'t make it'),
        ('maybe', 'Maybe'),
    ]
    
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    guest_count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    dietary_restrictions = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('party', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
