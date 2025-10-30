#!/usr/bin/env python
"""
Delete broken photo references (non-interactive)
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birthday.settings')
django.setup()

from birthdayapi.models import PartyPhoto

# Find and delete photos with missing files
broken_photos = []
all_photos = PartyPhoto.objects.all()

print(f"Checking {all_photos.count()} photos...")

for photo in all_photos:
    if photo.image:
        try:
            if not os.path.exists(photo.image.path):
                broken_photos.append(photo)
        except Exception as e:
            print(f"[ERROR] Photo {photo.id}: {e}")
            broken_photos.append(photo)

print(f"\nFound {len(broken_photos)} broken photo references")

if broken_photos:
    print("\nDeleting broken references...")
    deleted_count = 0
    for photo in broken_photos:
        try:
            photo.delete()
            deleted_count += 1
            print(f"[DELETED] Photo ID {photo.id}")
        except Exception as e:
            print(f"[ERROR] Could not delete photo ID {photo.id}: {e}")
    
    print(f"\n[SUCCESS] Deleted {deleted_count} broken photo references!")
    print(f"Remaining photos: {PartyPhoto.objects.count()}")
else:
    print("[OK] No broken photos found!")

print("\nChecking remaining photos...")
remaining = PartyPhoto.objects.all()
for photo in remaining:
    if photo.image:
        exists = os.path.exists(photo.image.path)
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} ID {photo.id}: {photo.image.name}")
