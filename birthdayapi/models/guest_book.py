from django.db import models
from django.contrib.auth.models import User

class GuestBookEntry(models.Model):
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='guest_book_entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Guest Book Entries"
    
    def __str__(self):
        return f"Message by {self.author.username} for {self.party.name}"
