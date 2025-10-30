# How to Add Photos Back

Since you manually deleted the photo files from the `media/party_photos/` directory, you'll need to re-upload them through your frontend application.

## Quick Steps

### Via Your Frontend App:

1. **Make sure you're logged in** with your Firebase account
   - You're now an admin, so you have full permissions!

2. **Navigate to the photo upload section** in your Birthday app

3. **Upload the photos again**:
   - Select the photos you want to add
   - Add captions if desired
   - Click upload

### Check What's Currently in Database:

The database still has references to the deleted photos, but the actual image files are missing. You have two options:

#### Option 1: Keep Current Database Entries (Recommended if you want to keep metadata)

Just re-upload the photos - they'll get new file paths automatically.

#### Option 2: Clean Up Broken References

If you want to remove the database entries for photos that no longer have files:

```bash
python manage.py shell
```

Then run:
```python
from birthdayapi.models import PartyPhoto
import os
from django.conf import settings

# Find photos with missing files
broken_photos = []
for photo in PartyPhoto.objects.all():
    if photo.image and not os.path.exists(photo.image.path):
        broken_photos.append(photo)
        print(f"Broken: {photo.id} - {photo.image.name}")

# If you want to delete them:
if broken_photos:
    confirm = input(f"Delete {len(broken_photos)} broken photo entries? (yes/no): ")
    if confirm.lower() == 'yes':
        for photo in broken_photos:
            photo.delete()
        print(f"Deleted {len(broken_photos)} broken photo entries")
else:
    print("No broken photos found!")
```

## Current Status

✅ **Your user is now an admin** - You can upload AND delete photos  
✅ **Upload functionality works** - Just use your frontend  
⚠️ **Only 1 photo file remains** on disk: `IMG_1908_3yqhvjw.JPG`  

## Next Steps

1. Open your frontend Birthday app
2. Log in (you're now an admin!)
3. Upload the photos you deleted
4. They'll be stored in `media/party_photos/` automatically

## Photo Storage After Upload

New uploads will be stored as:
```
media/party_photos/
  ├── IMG_1908_3yqhvjw.JPG  (existing)
  ├── {your-new-photos-here}.jpg
  └── ...
```

## Need Help?

- Frontend upload not working? Check `FRONTEND_INTEGRATION.md`
- Want to delete photos? Check `ADMIN_DELETE_PHOTOS.md`
- Storage questions? Check `STORAGE_INFO.md`
