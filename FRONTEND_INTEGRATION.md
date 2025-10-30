# Frontend Integration Quick Reference

## Backend Status: ✅ READY

Your Django backend is fully configured for Firebase authentication with:
- ✅ Firebase Admin SDK initialized
- ✅ Photo upload with user tracking
- ✅ Like/Heart feature working
- ✅ Authentication required for all photo operations
- ✅ CORS configured for localhost:3000

## Next Steps for Frontend

### 1. Install Dependencies (if not already)
```bash
npm install firebase
```

### 2. Firebase Configuration

Create/update `.env.local` in your Birthday-Client repo:

```env
NEXT_PUBLIC_FIREBASE_PROJECT_ID=birthday-ivy
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=birthday-ivy.firebaseapp.com
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=birthday-ivy.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
```

### 3. API Configuration

Add to `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Frontend Integration Code

#### Firebase Auth Setup
```javascript
// lib/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

#### API Helper with Auth
```javascript
// lib/api.js
import { auth } from './firebase';

export async function getAuthToken() {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken(true); // Force refresh
  }
  return null;
}

export async function apiRequest(endpoint, options = {}) {
  const token = await getAuthToken();
  
  const config = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  };

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, config);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}
```

#### Photo Operations
```javascript
// hooks/usePhotos.js
import { useState, useEffect } from 'react';
import { apiRequest, getAuthToken } from '../lib/api';

export function usePhotos() {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPhotos();
  }, []);

  async function loadPhotos() {
    try {
      const data = await apiRequest('/api/photos/');
      setPhotos(data);
    } catch (error) {
      console.error('Failed to load photos:', error);
    } finally {
      setLoading(false);
    }
  }

  async function uploadPhoto(partyId, imageFile, caption) {
    const token = await getAuthToken();
    const formData = new FormData();
    formData.append('party', partyId);
    formData.append('image', imageFile);
    formData.append('caption', caption);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/photos/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (response.ok) {
      const newPhoto = await response.json();
      setPhotos([newPhoto, ...photos]);
      return newPhoto;
    }
    throw new Error('Upload failed');
  }

  async function likePhoto(photoId) {
    try {
      const data = await apiRequest(`/api/photos/${photoId}/like/`, {
        method: 'POST',
      });
      loadPhotos(); // Reload to update like status
      return data;
    } catch (error) {
      console.error('Failed to like photo:', error);
    }
  }

  async function unlikePhoto(photoId) {
    try {
      await apiRequest(`/api/photos/${photoId}/unlike/`, {
        method: 'DELETE',
      });
      loadPhotos(); // Reload to update like status
    } catch (error) {
      console.error('Failed to unlike photo:', error);
    }
  }

  return { photos, loading, uploadPhoto, likePhoto, unlikePhoto, reload: loadPhotos };
}
```

#### Photo Display Component
```jsx
// components/PhotoGallery.jsx
import { usePhotos } from '../hooks/usePhotos';
import { auth } from '../lib/firebase';

export default function PhotoGallery() {
  const { photos, loading, likePhoto, unlikePhoto } = usePhotos();
  const user = auth.currentUser;

  if (loading) return <div>Loading photos...</div>;
  if (!user) return <div>Please log in to view photos</div>;

  return (
    <div className="photo-gallery">
      {photos.map(photo => (
        <div key={photo.id} className="photo-card">
          <img src={photo.image} alt={photo.caption} />
          <p>{photo.caption}</p>
          
          {/* Uploader Info */}
          <div className="uploader-info">
            Uploaded by: {photo.uploaded_by.full_name || photo.uploaded_by.username}
          </div>
          
          {/* Like Button */}
          <button
            onClick={() => photo.is_liked ? unlikePhoto(photo.id) : likePhoto(photo.id)}
            className={photo.is_liked ? 'liked' : ''}
          >
            ❤️ {photo.likes_count}
          </button>
        </div>
      ))}
    </div>
  );
}
```

#### Upload Component
```jsx
// components/PhotoUpload.jsx
import { useState } from 'react';
import { usePhotos } from '../hooks/usePhotos';

export default function PhotoUpload({ partyId }) {
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState('');
  const [uploading, setUploading] = useState(false);
  const { uploadPhoto, reload } = usePhotos();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await uploadPhoto(partyId, file, caption);
      setFile(null);
      setCaption('');
      reload();
    } catch (error) {
      alert('Upload failed. Please try again.');
      console.error(error);
    } finally {
      setUploading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files[0])}
        required
      />
      <textarea
        placeholder="Add a caption..."
        value={caption}
        onChange={(e) => setCaption(e.target.value)}
      />
      <button type="submit" disabled={uploading || !file}>
        {uploading ? 'Uploading...' : 'Upload Photo'}
      </button>
    </form>
  );
}
```

## Testing Checklist

- [ ] User can log in with Firebase
- [ ] Photos load when logged in
- [ ] Photos show uploader information
- [ ] User can upload photos
- [ ] User can like photos (heart icon)
- [ ] Like count updates correctly
- [ ] User can unlike photos
- [ ] Photos require authentication

## Common Issues

### "Invalid Firebase token"
- Ensure token is fresh: use `getIdToken(true)`
- Verify Firebase project IDs match

### CORS errors
- Backend allows localhost:3000
- Check browser console for specific CORS error

### Photo upload fails
- Verify file is valid image
- Check party ID is correct
- Ensure user is authenticated

## Support

See full API documentation in `API_DOCUMENTATION.md`
