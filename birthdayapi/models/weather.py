from django.db import models

class WeatherData(models.Model):
    party = models.OneToOneField('Party', on_delete=models.CASCADE, related_name='weather')
    temperature = models.IntegerField()  # Fahrenheit
    condition = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)  # Emoji or icon code
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Weather for {self.party.name}: {self.temperature}°F, {self.condition}"
