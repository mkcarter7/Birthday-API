# How to Delete Photos (Admin Only)

Photos can now only be deleted by admin users. Here are two ways to do it:

## Method 1: Django Admin Interface (Easiest) 🎯

1. **Create an admin user** (if you don't have one):
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create username, email, and password.

2. **Start the Django server**:
   ```bash
   python manage.py runserver
   ```

3. **Access the admin panel**:
   ```
   http://localhost:8000/admin/
   ```

4. **Log in** with your admin credentials.

5. **Navigate to Party Photos**:
   - Click on "Party Photos" under "BIRTHDAYAPI"

6. **Select and delete photos**:
   - Check the boxes next to the photos you want to delete
   - Choose "Delete selected party photos" from the action dropdown
   - Click "Go"
   - Confirm the deletion

**Note**: When you delete via the admin interface, the actual image files are automatically deleted from the server as well (see `admin.py` for the custom delete method).

## Method 2: API (Admin Users Only)

Only users with `is_staff=True` or `is_superuser=True` can delete photos via the API.

### Delete a single photo:
```bash
DELETE /api/photos/{id}/
Authorization: Bearer <admin-user-firebase-token>
```

### Example with curl:
```bash
curl -X DELETE \
  http://localhost:8000/api/photos/5/ \
  -H "Authorization: Bearer YOUR_ADMIN_FIREBASE_TOKEN"
```

### Example with JavaScript:
```javascript
// Get admin user's Firebase token
const token = await adminUser.getIdToken();

// Delete photo
const response = await fetch(`http://localhost:8000/api/photos/${photoId}/`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.ok) {
  console.log('Photo deleted successfully');
} else if (response.status === 403) {
  console.log('You do not have permission to delete photos');
}
```

## Making a User an Admin

### Via Django Shell:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Make a user an admin
user = User.objects.get(username='firebase-uid-here')
user.is_staff = True
user.is_superuser = True
user.save()

print(f"{user.username} is now an admin")
```

### Via Django Admin:
1. Go to `http://localhost:8000/admin/`
2. Click "Users" under "AUTHENTICATION AND AUTHORIZATION"
3. Click on the user you want to make admin
4. Check both:
   - ✅ Staff status
   - ✅ Superuser status
5. Click "Save"

## Permission Summary

### Photo Permissions:
- ✅ **View photos**: Anyone (public)
- ✅ **Upload photos**: Authenticated users
- ✅ **Like photos**: Authenticated users
- ❌ **Delete photos**: Admin users only

### Why This Helps:
- Prevents accidental deletion by regular users
- Protects photo gallery integrity
- Admins can moderate content
- Easy bulk deletion via admin interface

## Troubleshooting

### "You do not have permission to delete photos"
This means the user is not an admin. Make them an admin using one of the methods above.

### "Cannot find the photo"
The photo was already deleted or doesn't exist. Check the database or admin panel.

### Photo still showing in gallery
- Check if cached on frontend
- Verify database record was deleted
- Confirm media file was removed

## Safety Features

The admin interface includes:
- **Custom delete method** that removes both database record AND file
- **Confirmation dialog** before deletion
- **Bulk actions** for efficient management
- **Search and filters** to find specific photos quickly
