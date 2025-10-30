#!/usr/bin/env python
"""
Script to clean up broken photo references in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'birthday.settings')
django.setup()

from birthdayapi.models import PartyPhoto
from django.conf import settings

# Find photos with missing files
broken_photos = []
all_photos = PartyPhoto.objects.all()

print(f"Checking {all_photos.count()} photos...")

for photo in all_photos:
    if photo.image:
        try:
            # Try to access the file
            if os.path.exists(photo.image.path):
                print(f"[OK] {photo.id}: {photo.image.name} - EXISTS")
            else:
                print(f"[MISSING] {photo.id}: {photo.image.name} - MISSING")
                broken_photos.append(photo)
        except Exception as e:
            print(f"[ERROR] {photo.id}: {photo.image.name} - ERROR: {e}")
            broken_photos.append(photo)

print(f"\n{'='*60}")
print(f"Found {len(broken_photos)} broken photo references")

if broken_photos:
    print("\nBroken photos:")
    for photo in broken_photos:
        print(f"  - ID {photo.id}: {photo.image.name}")
        if photo.caption:
            print(f"    Caption: {photo.caption[:50]}")
        if photo.uploaded_by:
            print(f"    Uploaded by: {photo.uploaded_by.username}")
    
    # Ask for confirmation
    print(f"\n{'='*60}")
    response = input(f"\nDelete {len(broken_photos)} broken photo references? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        deleted_count = 0
        for photo in broken_photos:
            try:
                photo.delete()
                deleted_count += 1
                print(f"[DELETED] Photo ID {photo.id}")
            except Exception as e:
                print(f"[ERROR] Error deleting photo ID {photo.id}: {e}")
        
        print(f"\n[SUCCESS] Deleted {deleted_count} broken photo references!")
        print(f"Remaining photos: {PartyPhoto.objects.count()}")
    else:
        print("Cancelled. No photos were deleted.")
else:
    print("[OK] No broken photos found! Your database is clean.")
