from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class GuestBookEntry(models.Model):
    """
    Simple guest book entry model for birthday parties.
    Users can add, edit, and delete their own messages.
    """
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='guest_book_entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guest_book_entries')
    name = models.CharField(max_length=255, blank=True, help_text="Display name for the guest book entry")
    message = models.TextField(help_text="The guest book message")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Guest Book Entries"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['party', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message by {self.name} ({self.author.username}) for {self.party.name}"
    
    def is_author(self, user):
        """Check if the given user is the author of this entry"""
        return self.author == user
