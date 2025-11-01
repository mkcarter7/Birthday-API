# Backend Admin Security Setup

## ✅ Current Status: SECURED

All backend admin features are now properly secured with server-side validation.

## Security Implementation

### Admin Permission Checks Applied

#### 1. **RSVP Management** (`birthdayapi/views/rsvp.py`)
- ✅ **GET `/api/rsvps/`**: Only admins see all RSVPs, regular users only see their own
- ✅ **GET `/api/rsvps/party_summary/`**: Only admins, party hosts, or participants can view
- ✅ Users can only update/delete their own RSVPs

```python
def get_queryset(self):
    queryset = RSVP.objects.all()
    
    # SECURITY: Only admins can see all RSVPs
    if not self.request.user.is_staff:
        queryset = queryset.filter(user=self.request.user)
    
    # ... rest of filtering
```

#### 2. **Photo Management** (`birthdayapi/views/photo.py`)
- ✅ **DELETE `/api/photos/{id}/`**: Only admins can delete photos
- ✅ Anyone can view and upload photos
- ✅ Anyone can like photos

```python
def get_permissions(self):
    if self.action in ['list', 'retrieve', 'party_gallery']:
        return [AllowAny()]
    elif self.action in ['destroy']:
        return [IsAdminUser()]  # Only admins can delete
    else:
        return [IsAuthenticated()]
```

#### 3. **Badge Management** (`birthdayapi/views/badges.py`)
- ✅ **POST/PUT/PATCH/DELETE `/api/badges/`**: Only admins can create/update/delete badges
- ✅ Anyone can view badges

```python
def get_permissions(self):
    if self.action in ['create', 'update', 'partial_update', 'destroy']:
        permission_classes = [IsAdminUser]
    else:
        permission_classes = [IsAuthenticated]
    return [permission() for permission in permission_classes]
```

#### 4. **Game Score Management** (`birthdayapi/views/game_score.py`)
- ✅ **GET `/api/scores/`**: Regular users only see their own scores, staff see all
- ✅ Users can only update/delete their own scores

```python
def get_queryset(self):
    queryset = GameScore.objects.select_related('user', 'party')
    
    # Regular users can only see their own scores, staff can see all
    if not self.request.user.is_staff:
        queryset = queryset.filter(user=self.request.user)
```

#### 5. **User Badge Awards** (`birthdayapi/views/badges.py`)
- ✅ Only staff can award badges to other users
- ✅ Users can earn badges for themselves if they have enough points

```python
# Only staff can award badges to other users
if user != request.user.id and not request.user.is_staff:
    return Response(
        {'error': 'You can only earn badges for yourself.'},
        status=status.HTTP_403_FORBIDDEN
    )
```

### Admin Status Check Endpoint

**Endpoint**: `GET /api/check-admin/`

**Authentication**: Required (Firebase token)

**Response**:
```json
{
  "is_admin": true,
  "is_staff": true,
  "is_superuser": false,
  "username": "user@example.com",
  "email": "user@example.com"
}
```

**Usage in Frontend**:
```javascript
const checkAdminStatus = async (token) => {
  const response = await fetch('http://localhost:8000/api/check-admin/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    return data.is_admin;
  }
  return false;
};
```

## Making Users Admin

### Method 1: Django Admin Panel
1. Navigate to `http://localhost:8000/admin`
2. Click **Users** under **AUTHENTICATION AND AUTHORIZATION**
3. Select the user
4. Check **"Staff status"** or **"Superuser status"**
5. Save

### Method 2: Django Shell
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Make user admin by username
user = User.objects.get(username='firebase-uid-here')
user.is_staff = True
user.is_superuser = True
user.save()

print(f"{user.username} is now an admin")
```

### Method 3: Update Existing User by Email
```python
from django.contrib.auth.models import User

# Find user by email
user = User.objects.get(email='admin@example.com')
user.is_staff = True
user.save()

print(f"{user.email} is now staff")
```

## Admin Permission Levels

### `is_staff`
- Access to Django admin interface
- Access to admin-only API endpoints
- Can moderate content

### `is_superuser`
- All `is_staff` privileges
- Bypass all permission checks
- Full system access

**Recommendation**: Use `is_staff=True` for party administrators, reserve `is_superuser=True` for system administrators.

## Security Checklist

- ✅ RSVP list filtered by user/admin status
- ✅ Photo deletion requires admin
- ✅ Badge management requires admin
- ✅ Game score access restricted by user/admin status
- ✅ User badge awards restricted by admin status
- ✅ Admin status endpoint available
- ✅ All endpoints return 403 for unauthorized access
- ✅ Frontend can check admin status via API

## Testing Admin Access

### Test as Regular User
```bash
# Should only see own RSVPs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/rsvps/

# Should fail with 403
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/photos/1/
```

### Test as Admin
```bash
# Should see all RSVPs
curl -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/api/rsvps/

# Should succeed
curl -X DELETE \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  http://localhost:8000/api/photos/1/
```

## Frontend Integration

### Updated Admin Utility

```javascript
// src/utils/admin.js
import { auth } from '../config/firebase';

export const isAdmin = async (user) => {
  if (!user) return false;
  
  try {
    const token = await user.getIdToken();
    const response = await fetch('http://localhost:8000/api/check-admin/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.is_admin || false;
    }
  } catch (error) {
    console.error('Error checking admin status:', error);
  }
  
  return false;
};

// Usage
const adminStatus = await isAdmin(auth.currentUser);
if (adminStatus) {
  // Show admin features
}
```

## Security Best Practices

1. **Never trust client-side checks alone** - Always validate on backend
2. **Use HTTPS in production** - Protect tokens in transit
3. **Limit admin users** - Only grant to trusted individuals
4. **Regular audits** - Periodically review admin list
5. **Use least privilege** - Grant `is_staff` instead of `is_superuser` when possible
6. **Monitor admin actions** - Consider logging admin activities

## Troubleshooting

### "You do not have permission" (403)
- User is not marked as admin
- Check user's `is_staff` or `is_superuser` status
- Verify token is being sent correctly

### Admin endpoint returns false
- User account not found in Django
- Firebase UID doesn't match Django username
- Check user creation in authentication flow

### Can still access admin features after removing admin status
- Clear frontend cache/localStorage
- Refresh authentication token
- Restart Django server if needed

## Next Steps

- ✅ Backend security implemented
- ✅ Admin status endpoint created
- ✅ All admin features secured
- 🔄 Frontend should integrate `/api/check-admin/` endpoint
- 🔄 Frontend should handle 403 errors gracefully
