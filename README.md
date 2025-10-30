# BIRTHDAY API

## ABOUT
Django REST API for managing birthday parties with Firebase authentication. Integrated with Next.js frontend ([Birthday-Client](https://github.com/mkcarter7/Birthday-Client)).

## FEATURES
- 🔐 Firebase Authentication (users must log in to view/add photos)
- 📸 Photo Management with User Tracking
- ❤️ Like/Heart System for Photos
- 📋 RSVP System
- 🎁 Gift Registry
- 📝 Guest Book
- 🎮 Games & Badges
- ⏰ Timeline & Weather
- 💰 Venmo Integration

## INSTALLATION

### Prerequisites
- Python 3.9+
- Firebase Account
- pip or pipenv

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/mkcarter7/Birthday-API.git
cd Birthday-API
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create `.env` file in project root:
```env
FIREBASE_PROJECT_ID=birthday-ivy
FIREBASE_CLIENT_EMAIL=your-service-account@birthday-ivy.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_CLIENT_ID=your-client-id
```

4. **Set up database**
```bash
python manage.py migrate
```

5. **Run the server**
```bash
python manage.py runserver
```

Server will be available at `http://localhost:8000`

## API DOCUMENTATION

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API reference.

See [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) for Next.js integration guide.

## TECH STACK
- **Backend**: Django, Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Firebase Admin SDK
- **Media Storage**: Local (development) / Cloud Storage (production)
- **Frontend**: Next.js (separate repo)

## ENDPOINTS

### Photo Management (Requires Authentication)
- `GET /api/photos/` - Get all photos
- `POST /api/photos/` - Upload photo
- `POST /api/photos/{id}/like/` - Like photo
- `DELETE /api/photos/{id}/unlike/` - Unlike photo
- `POST /api/photos/{id}/toggle_featured/` - Toggle featured status

### Other Endpoints
- `GET /api/parties/` - List parties
- `GET /api/rsvps/` - RSVPs
- `GET /api/gifts/` - Gift registry
- `GET /api/guestbook/` - Guest book entries

## CONTRIBUTORS
- https://github.com/mkcarter7

## LICENSE
MIT
