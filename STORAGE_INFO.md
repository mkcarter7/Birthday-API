# Photo Storage Information

## Storage Location

### Development
- **Local Path**: `C:\Users\mkdpr\projects\Birthday-API\media\party_photos\`
- **URL**: `http://localhost:8000/media/party_photos/{filename}`
- **Full Example**: `http://localhost:8000/media/party_photos/IMG_1908.JPG`

### Current Photos
You have **9 photos** in storage:
1. IMG_1908.JPG
2. IMG_1908_3yqhvjw.JPG
3. IMG_1908_7fMSwfg.JPG
4. IMG_1908_9WZMbE8.JPG
5. IMG_1908_nHFOZft.JPG
6. IMG_1908_r60TavQ.JPG
7. IMG_1908_uyWM24w.JPG
8. IMG_1908_VHZbqrs.JPG
9. IMG_1908_yWQ8zuF.JPG

## Configuration

### Settings (birthday/settings.py)
```python
# Media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Model (birthdayapi/models/photo.py)
```python
image = models.ImageField(upload_to='party_photos/')
```

### URL Configuration
Media files are served in development via:
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Accessing Photos

### Via API
```bash
# Get all photos
GET http://localhost:8000/api/photos/

# Get specific photo metadata
GET http://localhost:8000/api/photos/{id}/

# Direct file access
GET http://localhost:8000/media/party_photos/IMG_1908.JPG
```

### Via Browser
Just paste the URL in your browser:
```
http://localhost:8000/media/party_photos/IMG_1908.JPG
```

## Production Deployment

For production, you'll need to:

1. **Use a cloud storage service** (AWS S3, Google Cloud Storage, etc.)
2. **Install django-storages**:
   ```bash
   pip install django-storages boto3
   ```
3. **Update settings.py**:
   ```python
   INSTALLED_APPS = [
       ...
       'storages',
   ]
   
   # For AWS S3
   AWS_ACCESS_KEY_ID = 'your-key'
   AWS_SECRET_ACCESS_KEY = 'your-secret'
   AWS_STORAGE_BUCKET_NAME = 'your-bucket'
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   ```

## Database Reference

Photos are stored in the database with:
- **Model**: `PartyPhoto`
- **Table**: `birthdayapi_partyphoto`
- **Fields**:
  - `id` - Primary key (AutoField)
  - `party` - Foreign key to Party
  - `image` - Path to the file
  - `caption` - Optional caption
  - `uploaded_at` - Timestamp
  - `uploaded_by` - User who uploaded (ForeignKey)
  - `is_featured` - Boolean flag

## Permissions

Current configuration:
- ✅ **View photos**: Public (anyone can access)
- 🔐 **Upload photos**: Authenticated users only
- 🔐 **Like photos**: Authenticated users only
- 🔐 **Delete photos**: Authenticated users only

## Troubleshooting

### Photos not showing?
1. Check Django server is running
2. Verify `DEBUG = True` in settings (for local file serving)
3. Check file exists in `media/party_photos/`
4. Verify URL pattern includes static files

### Permission errors?
1. Ensure file has correct permissions
2. Check Django can write to `media/` directory
3. Verify `MEDIA_ROOT` path is correct

### Need to move photos?
```bash
# Backup existing photos
cp -r media/ media_backup/

# Or on Windows
xcopy media media_backup /E /I
```
