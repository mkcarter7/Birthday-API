# Django Superuser Setup Guide

## 🎉 Good News!

You already have **2 superuser accounts** set up:
- ✅ `admin` - Has password, can log in to admin panel
- ✅ `TLttgOo55jgtvuRerfRzt6vpxWo1` - Your Firebase user (needs password to log in)

## Quick Access

**Django Admin Panel**: http://localhost:8000/admin

**Login with admin account:**
- Username: `admin`
- Password: (the password you set when creating it)

**To log in with your Firebase account**, you need to set a password first:

```bash
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='TLttgOo55jgtvuRerfRzt6vpxWo1'); u.set_password('YourSecurePassword123!'); u.save(); print('Password set successfully')"
```

---

## Setup Guide

### Creating a New Superuser

In your terminal, from the Django project directory (`Birthday-API/`), run:

```bash
python manage.py createsuperuser
```

You'll be prompted for:
- **Username**: Can be email or username
- **Email address**: Your email
- **Password**: Enter twice (won't show on screen for security)

**Example:**
```bash
$ python manage.py createsuperuser
Username: admin@birthdayparty.com
Email address: admin@birthdayparty.com
Password: 
Password (again): 
Superuser created successfully.
```

### Making an Existing User a Superuser

If you already have a user account (created via Firebase auth), convert it to superuser:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.contrib.auth.models import User

# Find your user by username (Firebase UID) or email
user = User.objects.get(username='your-firebase-uid')
# OR by email if you know it
# user = User.objects.filter(email='your@email.com').first()

# Make them superuser
user.is_superuser = True
user.is_staff = True
user.save()

# Verify
print(f"User {user.username} is now superuser: {user.is_superuser}")
print(f"User {user.username} is now staff: {user.is_staff}")

# Exit
exit()
```

**One-liner version:**
```bash
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='YOUR_FIREBASE_UID'); u.is_superuser = True; u.is_staff = True; u.save(); print('Superuser created')"
```

Replace `YOUR_FIREBASE_UID` with your actual Firebase UID.

## Finding Your Firebase UID

### From Your Frontend
Your Firebase authentication will provide a UID. Check your authentication token or Firebase console.

### From Database
```python
python manage.py shell -c "from django.contrib.auth.models import User; [print(f'ID: {u.id}, Username: {u.username}, Email: {u.email}') for u in User.objects.all()]"
```

## Logging In

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to: **http://localhost:8000/admin**

3. Use your credentials:
   - **Username**: Your Firebase UID (if created via Firebase auth) or email/username you set
   - **Password**: The password you set when creating superuser

## Firebase Auth Users

If your users are created via Firebase authentication, they won't have a password set. You need to either:

### Option 1: Set a Password for Existing User
```python
python manage.py shell
```

```python
from django.contrib.auth.models import User

user = User.objects.get(username='firebase-uid-here')
user.set_password('your_secure_password')
user.is_superuser = True
user.is_staff = True
user.save()

print(f"User {user.username} can now log in with password")
```

### Option 2: Create New Superuser Account
Create a completely separate admin account:
```bash
python manage.py createsuperuser
```

Use a different username/email than your Firebase account.

## Verification

### Check If User Is Admin
```python
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Check all admin users
admins = User.objects.filter(is_superuser=True)
for admin in admins:
    print(f"Admin: {admin.username}, Staff: {admin.is_staff}, Superuser: {admin.is_superuser}")

# Or check specific user
user = User.objects.get(username='firebase-uid-here')
print(f"Is staff: {user.is_staff}")
print(f"Is superuser: {user.is_superuser}")
```

### Test Admin Access via API
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/check-admin/
```

Should return:
```json
{
  "is_admin": true,
  "is_staff": true,
  "is_superuser": true,
  "username": "your-username",
  "email": "your@email.com"
}
```

## Common Issues

### "Command not found: python"
Try:
```bash
python3 manage.py createsuperuser
```

### "Could not import django module"
Make sure you're in the Django project directory:
```bash
cd ~/projects/Birthday-API  # Adjust to your path
python manage.py createsuperuser
```

### "You must use --run-syncdb"
Run migrations first:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### "No such user exists"
List all users:
```python
python manage.py shell -c "from django.contrib.auth.models import User; [print(f'{u.id}: {u.username} ({u.email})') for u in User.objects.all()]"
```

### "Invalid username or password"
Firebase users don't have passwords. Set one or create new superuser.

### Forgot Admin Password
Reset your admin password:
```bash
python manage.py changepassword admin
```

Or reset via shell:
```python
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('YourNewPassword123!'); u.save(); print('Password reset successfully')"
```

### Can't Log In After Making User Superuser
1. Make sure `is_staff = True` AND `is_superuser = True`
2. Set a password for the user
3. Log out and log back in
4. Clear browser cache

## Admin vs Staff vs Superuser

| Type | Django Admin Access | API Admin Endpoints | Full System Access |
|------|---------------------|---------------------|-------------------|
| `is_staff=True` | ✅ Yes | ✅ Yes | ❌ No |
| `is_superuser=True` | ✅ Yes | ✅ Yes | ✅ Yes |
| Both | ✅ Yes | ✅ Yes | ✅ Yes |

**Recommendation**: For party admins, use `is_staff=True`. For system administrators, use `is_superuser=True`.

## Security Best Practices

1. **Use strong passwords** - At least 12 characters with mix of letters, numbers, symbols
2. **Limit superusers** - Only grant to trusted individuals
3. **Use 2FA** - Consider enabling two-factor authentication for admin accounts
4. **Regular audits** - Periodically review who has admin access
5. **Separate accounts** - Keep Firebase user accounts separate from admin accounts
6. **HTTPS only** - Never access admin panel over HTTP in production

## Quick Commands Reference

```bash
# Create superuser
python manage.py createsuperuser

# List all users
python manage.py shell -c "from django.contrib.auth.models import User; [print(f'{u.username} - Staff: {u.is_staff}, Super: {u.is_superuser}') for u in User.objects.all()]"

# Make existing user superuser
python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='UID'); u.is_staff=True; u.is_superuser=True; u.save()"

# Check if admin
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/check-admin/
```

## Next Steps

After creating superuser:
1. ✅ Log in to Django admin at `/admin`
2. ✅ Test admin API endpoints
3. ✅ Review existing data
4. ✅ Configure admin interface preferences
5. ✅ Set up additional staff users as needed

## Troubleshooting

If you're still having issues, check:
1. Is the Django server running?
2. Are you in the correct directory?
3. Have you run migrations? (`python manage.py migrate`)
4. Is the user object saved? (did you call `.save()`)
5. Have you cleared cache/cookies?
6. Is the database accessible?

For more help, see `BACKEND_ADMIN_SECURITY.md`
