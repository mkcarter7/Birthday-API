from django.db import models

class PartyTimelineEvent(models.Model):
    party = models.ForeignKey('Party', on_delete=models.CASCADE, related_name='timeline_events')
    time = models.TimeField()
    activity = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, blank=True)  # Emoji
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['time']
    
    def __str__(self):
        return f"{self.time} - {self.activity}"
