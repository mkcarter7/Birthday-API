from django.db import models
from django.contrib.auth.models import User

class GameScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    party = models.ForeignKey('Party', on_delete=models.CASCADE)
    total_points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'party')
    
    def __str__(self):
        return f"{self.user.username} - {self.total_points} points"
    
    def calculate_level(self):
        """Calculate level based on points (every 100 points = 1 level)"""
        return (self.total_points // 100) + 1
