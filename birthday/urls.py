"""
Birthday API URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from birthdayapi.views.party import PartyViewSet
from birthdayapi.views.photo import PartyPhotoViewSet
from birthdayapi.views.rsvp import RSVPViewSet
from birthdayapi.views.gift_registry import GiftRegistryItemViewSet
from birthdayapi.views.guest_book import GuestBookEntryViewSet
from birthdayapi.views.game_score import GameScoreViewSet
from birthdayapi.views.badges import BadgeViewSet

router = DefaultRouter()
router.register(r'api/parties', PartyViewSet, basename='party')
router.register(r'api/photos', PartyPhotoViewSet, basename='partyphoto')
router.register(r'api/rsvps', RSVPViewSet, basename='rsvp')
router.register(r'api/gifts', GiftRegistryItemViewSet, basename='giftregistryitem')
router.register(r'api/guestbook', GuestBookEntryViewSet, basename='guestbookentry')
router.register(r'api/scores', GameScoreViewSet, basename='gamescore')
router.register(r'api/badges', BadgeViewSet, basename='badge')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/auth/', include('rest_framework.urls')),
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
