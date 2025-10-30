from django.db import models
from django.contrib.auth.models import User

class PartyPhoto(models.Model):
    id = models.AutoField(primary_key=True)  # Explicit primary key
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='party_photos/')
    caption = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_photos')
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Photo for {self.party.name}"
    
    @property
    def likes_count(self):
        return self.likes.count()

class PhotoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_likes')
    photo = models.ForeignKey(PartyPhoto, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'photo']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.photo}"
