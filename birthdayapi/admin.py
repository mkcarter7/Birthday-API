from django.contrib import admin
from .models import Party, PartyPhoto, PhotoLike, RSVP, GuestBookEntry, GiftRegistryItem, Badge, UserBadge, GameScore

# Register Party model
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'host', 'date', 'location', 'is_active', 'is_public']
    list_filter = ['is_active', 'is_public', 'date']
    search_fields = ['name', 'location', 'host__username']
    date_hierarchy = 'date'

# Register PartyPhoto model
@admin.register(PartyPhoto)
class PartyPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'party', 'uploaded_by', 'uploaded_at', 'is_featured', 'caption']
    list_filter = ['is_featured', 'uploaded_at', 'party']
    search_fields = ['caption', 'party__name', 'uploaded_by__username']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['uploaded_at']
    
    def delete_model(self, request, obj):
        """Delete the file when deleting the photo"""
        if obj.image:
            obj.image.delete(save=False)
        super().delete_model(request, obj)

# Register PhotoLike model
@admin.register(PhotoLike)
class PhotoLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'photo', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'photo__caption']

# Register RSVP model
@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['party', 'user', 'status', 'guest_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'party__name']

# Register GuestBookEntry model
@admin.register(GuestBookEntry)
class GuestBookEntryAdmin(admin.ModelAdmin):
    list_display = ['party', 'author', 'created_at', 'updated_at']
    list_filter = ['created_at', 'party']
    search_fields = ['message', 'author__username', 'party__name']
    readonly_fields = ['created_at', 'updated_at']

# Register GiftRegistryItem model
@admin.register(GiftRegistryItem)
class GiftRegistryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'party', 'price', 'priority', 'is_purchased']
    list_filter = ['priority', 'is_purchased']
    search_fields = ['name', 'description']

# Register Badge model
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

# Register UserBadge model
@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'party', 'earned_at']
    list_filter = ['earned_at']
    search_fields = ['user__username']

# Register GameScore model
@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'party', 'total_points', 'level']
    list_filter = ['party', 'level']
    search_fields = ['user__username']
