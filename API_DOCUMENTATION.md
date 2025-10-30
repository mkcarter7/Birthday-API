# Birthday API Documentation - Frontend Integration Guide

## Overview
This Django REST API is configured to work with your Next.js frontend (`Birthday-Client`) using Firebase authentication. Users must be logged in to view and upload photos, and all photos are tracked with user information including a like/heart feature.

## Frontend & Backend Alignment

### Firebase Configuration ✅
Both your frontend and backend are configured for the Firebase project: **birthday-ivy**

### Frontend Setup (Birthday-Client Repo)
Your Next.js frontend should:
1. Use Firebase Client SDK for authentication
2. Send Firebase ID tokens in Authorization headers
3. Connect to Django API at: `http://localhost:8000` or your production URL

### Backend Setup ✅
Backend is configured and ready:
- Firebase Admin SDK initialized
- CORS enabled for localhost:3000
- Photo API requires authentication
- User tracking implemented

## API Endpoints

### Base URL
- Development: `http://localhost:8000`
- Production: Your deployed URL

### Authentication Headers
All authenticated endpoints require:
```
Authorization: Bearer <firebase-id-token>
```

### Photo Endpoints

#### 1. Get All Photos (Logged In Users Only)
```http
GET /api/photos/
```
**Authentication Required:** ✅ Yes  
**Returns:** List of all photos with uploader info

#### 2. Upload a Photo
```http
POST /api/photos/
Content-Type: multipart/form-data

Authorization: Bearer <firebase-id-token>
```
**Body:**
```javascript
FormData:
- party: <party-id>
- image: <file>
- caption: "Great party!"
- is_featured: false
```

**Returns:** Created photo object with uploader information

#### 3. Get Photos by Party
```http
GET /api/photos/?party=<party-id>
```

#### 4. Get User's Photos
```http
GET /api/photos/?my_photos=true
```

#### 5. Get Featured Photos
```http
GET /api/photos/?featured=true
```

#### 6. Like a Photo ❤️
```http
POST /api/photos/{id}/like/
```

#### 7. Unlike a Photo
```http
DELETE /api/photos/{id}/unlike/
```

#### 8. Toggle Featured Status
```http
POST /api/photos/{id}/toggle_featured/
```
**Note:** Only party host can feature photos

#### 9. Party Gallery
```http
GET /api/photos/party_gallery/?party_id=<party-id>
```

## Frontend Integration Example

### 1. Login with Firebase
```javascript
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const user = userCredential.user;
const idToken = await user.getIdToken();
```

### 2. Get Photos
```javascript
const response = await fetch('http://localhost:8000/api/photos/', {
  headers: {
    'Authorization': `Bearer ${idToken}`,
    'Content-Type': 'application/json'
  }
});

const photos = await response.json();
// Returns array of photos with:
// - id, image, caption, uploaded_at
// - uploaded_by (user info)
// - likes_count
// - is_liked (if current user liked it)
// - is_featured
```

### 3. Upload Photo
```javascript
const formData = new FormData();
formData.append('party', partyId);
formData.append('image', imageFile);
formData.append('caption', caption);

const response = await fetch('http://localhost:8000/api/photos/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${idToken}`
  },
  body: formData
});

const newPhoto = await response.json();
```

### 4. Like Photo ❤️
```javascript
const response = await fetch(`http://localhost:8000/api/photos/${photoId}/like/`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});

const result = await response.json();
// Returns: { message: 'Photo liked', likes_count: 5 }
```

### 5. Unlike Photo
```javascript
const response = await fetch(`http://localhost:8000/api/photos/${photoId}/unlike/`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});
```

## Photo Response Object
```javascript
{
  id: 1,
  party: 1,
  image: "http://localhost:8000/media/party_photos/image.jpg",
  caption: "Great party!",
  uploaded_at: "2025-01-30T12:00:00Z",
  uploaded_by: {
    id: 1,
    username: "firebase-uid",
    email: "user@example.com",
    full_name: "John Doe"
  },
  likes_count: 5,
  is_liked: true,  // Whether current user liked it
  is_featured: false,
  party_name: "Birthday Bash 2025"
}
```

## Error Handling

### Common Status Codes
- `200 OK` - Successful request
- `201 Created` - Successfully created resource
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid auth token
- `403 Forbidden` - Not allowed (e.g., not party host)
- `404 Not Found` - Resource not found

### Example Error Response
```javascript
{
  "detail": "Invalid Firebase token"
}
```

## User Tracking Features

### ✅ Implemented
- **Photo Uploader**: Every photo shows who uploaded it
- **User Info**: Display name, email, username
- **Like Tracking**: Shows if current user liked each photo
- **Like Count**: Total likes per photo

### User Information Display
When displaying photos, you can show:
```javascript
<div>
  <img src={photo.image} alt={photo.caption} />
  <p>{photo.caption}</p>
  <p>Uploaded by: {photo.uploaded_by.full_name}</p>
  <p>❤️ {photo.likes_count} likes</p>
  {photo.is_liked && <span>You liked this!</span>}
</div>
```

## CORS Configuration

Backend is configured to allow requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`
- Your production domains (update in settings.py if needed)

## Testing

### 1. Start Backend
```bash
cd Birthday-API
python manage.py runserver
```

### 2. Start Frontend
```bash
cd Birthday-Client
npm run dev
```

### 3. Test Flow
1. Log in via Firebase on frontend
2. Get ID token
3. Call API with token
4. Verify photos load and user info displays
5. Test upload and like features

## Production Deployment

### Environment Variables
- Backend `.env`: Firebase service account credentials
- Frontend `.env.local`: Firebase client config

### Firebase Projects
- Both must use same project: `birthday-ivy`
- Service account key from same project

### Security Notes
- Never commit `.env` or service account files
- Use environment variables in production
- HTTPS required in production
- Update CORS_ALLOWED_ORIGINS for production domains
