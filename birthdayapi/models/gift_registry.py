from django.db import models
from django.contrib.auth.models import User

class GiftRegistryItem(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Nice to Have'),
        ('medium', 'Would Love'),
        ('high', 'Really Want'),
    ]
    
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='gift_registry')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField(blank=True)
    image = models.ImageField(upload_to='gift_images/', blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Purchase tracking
    is_purchased = models.BooleanField(default=False)
    purchased_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    purchase_note = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', 'price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}"
