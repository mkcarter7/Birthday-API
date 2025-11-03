# Birthday API

A Django REST API for managing birthday parties with Firebase authentication. Designed to work seamlessly with Next.js frontend applications.

## 🎉 Features

- 🔐 **Firebase Authentication** - Secure user authentication and authorization
- 📸 **Photo Management** - Upload, view, and manage party photos with user tracking
- 📋 **RSVP System** - Manage party invitations and responses
- 🎁 **Gift Registry** - Create and manage gift wish lists
- 📝 **Guest Book** - Guests can leave messages and well-wishes
- 🎮 **Games & Badges** - Track game scores and award badges
- 🎯 **Trivia** - Interactive trivia questions for party entertainment

## 🛠️ Tech Stack

- **Backend Framework**: Django 4.2.8
- **API**: Django REST Framework 3.14.0
- **Authentication**: Firebase Admin SDK 6.4.0
- **Database**: SQLite (development) / PostgreSQL (production)
- **Image Processing**: Pillow 10.1.0
- **CORS**: django-cors-headers 4.3.1

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9+
- pip or pipenv
- Firebase Account (for authentication)
- Git

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mkcarter7/Birthday-API.git
cd Birthday-API
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using pipenv:

```bash
pipenv install
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_CLIENT_ID=your-client-id

# Django Settings (for production)
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

This allows you to access the Django admin panel at `/admin/`.

### 6. Run the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: Your deployed URL

### Authentication

All authenticated endpoints require a Firebase ID token in the Authorization header:

```
Authorization: Bearer <firebase-id-token>
```

### Available Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/parties/` | GET, POST | List/create parties | POST: Yes |
| `/api/photos/` | GET, POST | List/upload photos | Yes |
| `/api/photos/{id}/like/` | POST | Like a photo | Yes |
| `/api/photos/{id}/unlike/` | DELETE | Unlike a photo | Yes |
| `/api/photos/{id}/toggle_featured/` | POST | Toggle featured status | Yes (Host only) |
| `/api/rsvps/` | GET, POST | Manage RSVPs | Yes |
| `/api/gifts/` | GET, POST | Gift registry | Yes |
| `/api/guestbook/` | GET, POST | Guest book entries | POST: Yes |
| `/api/scores/` | GET, POST | Game scores | Yes |
| `/api/badges/` | GET | View badges | Yes |
| `/api/trivia/` | GET, POST | Trivia questions | Yes |
| `/api/check-admin/` | GET | Check admin status | Yes |
| `/admin/` | - | Django admin panel | Yes |

## 🔧 Configuration

### CORS Settings

The API is configured to allow requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`

For production, update `CORS_ALLOWED_ORIGINS` in `birthday/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
]
```

## 🧪 Testing

Run tests with pytest:

```bash
pytest
```

## 🔒 Security Notes

- Never commit `.env` files or Firebase service account keys
- Always use HTTPS in production
- Keep `DEBUG=False` in production
- Regularly update dependencies
- Use environment variables for sensitive data

## 🚀 Deployment

For production deployment:

1. Set `DEBUG=False` in settings or `.env`
2. Configure `ALLOWED_HOSTS` with your domain
3. Set up PostgreSQL or another production database
4. Configure cloud storage for media files
5. Set up proper CORS origins
6. Use a production WSGI server (gunicorn, uWSGI)

## 📄 License

This project is private and proprietary.

## 👤 Contributors

- [mkcarter7](https://github.com/mkcarter7)

## 🔗 Related Projects

- **Frontend**: [Birthday-Client](https://github.com/mkcarter7/Birthday-Client) - Next.js frontend application
