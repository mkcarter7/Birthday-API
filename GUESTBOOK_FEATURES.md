# Guest Book Features

## ✅ Core Features

A simple, clean guest book system where users can add, edit, and delete their own messages for birthday parties.

### Viewing Messages (Public)
Anyone can view guest book entries:
- `GET /api/guestbook/` - List all entries
- `GET /api/guestbook/{id}/` - Get single entry
- `GET /api/guestbook/my_entries/` - Get your own entries (authenticated)
- `GET /api/guestbook/?party={id}` - Filter by party
- `GET /api/guestbook/?search={query}` - Search in messages

### Adding Messages (Authenticated)
Logged-in users can add messages:
- `POST /api/guestbook/`
- Message automatically shows who added it
- User info includes: username, first_name, last_name

### Editing Messages (Author Only)
Users can edit ONLY their own messages:
- `PUT /api/guestbook/{id}/` - Update entire entry
- `PATCH /api/guestbook/{id}/` - Partial update
- Only the author can edit their own message
- Returns 403 if trying to edit someone else's message

### Deleting Messages (Author Only)
Users can delete ONLY their own messages:
- `DELETE /api/guestbook/{id}/`
- Only the author can delete their own message
- Returns 403 if trying to delete someone else's message

## User Information Display

Each message shows:
```json
{
  "id": 1,
  "party": 1,
  "party_name": "John's Birthday Bash",
  "author": 2,
  "author_username": "john_doe",
  "author_first_name": "John",
  "author_last_name": "Doe",
  "name": "John Doe",
  "message": "Happy birthday!",
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z",
  "can_edit": false
}
```

## API Examples

### Add a Message
```javascript
// POST /api/guestbook/
const response = await fetch('http://localhost:8000/api/guestbook/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    party: 1,  // Party ID
    name: "Custom Display Name",  // Optional - custom display name
    message: "Happy birthday! 🎉"
  })
});

const newMessage = await response.json();
// Returns message with your user info attached
```

### Edit Your Message
```javascript
// PATCH /api/guestbook/{id}/
const response = await fetch('http://localhost:8000/api/guestbook/5/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: "Updated message! 🎂"
  })
});

const updatedMessage = await response.json();
```

### Delete Your Message
```javascript
// DELETE /api/guestbook/{id}/
const response = await fetch('http://localhost:8000/api/guestbook/5/', {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

if (response.ok) {
  console.log('Message deleted successfully');
}
```

### Get All Messages (Public)
```javascript
// GET /api/guestbook/
const response = await fetch('http://localhost:8000/api/guestbook/');
const messages = await response.json();

messages.forEach(msg => {
  console.log(`${msg.author_first_name}: ${msg.message}`);
  console.log(`Posted ${msg.created_at}`);
});
```

### Get Messages by Party
```javascript
// GET /api/guestbook/?party=1
const response = await fetch('http://localhost:8000/api/guestbook/?party=1');
const messages = await response.json();
```

### Get My Messages
```javascript
// GET /api/guestbook/my_entries/
const response = await fetch('http://localhost:8000/api/guestbook/my_entries/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const myMessages = await response.json();
```

### Search Messages
```javascript
// GET /api/guestbook/?search=birthday
const response = await fetch('http://localhost:8000/api/guestbook/?search=birthday');
const messages = await response.json();
```

## Frontend Component Example

```jsx
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

function GuestBook({ partyId }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const { user, token } = useAuth();

  // Load messages
  useEffect(() => {
    fetch(`http://localhost:8000/api/guestbook/?party=${partyId}`)
      .then(res => res.json())
      .then(data => setMessages(data));
  }, [partyId]);

  // Add message
  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/api/guestbook/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        party: partyId,
        message: newMessage
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      setMessages([data, ...messages]);
      setNewMessage('');
    }
  };

  // Edit message
  const handleEdit = async (messageId, updatedMessage) => {
    const response = await fetch(`http://localhost:8000/api/guestbook/${messageId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: updatedMessage })
    });
    
    if (response.ok) {
      const data = await response.json();
      setMessages(messages.map(msg => msg.id === messageId ? data : msg));
      return data;
    }
    throw new Error('Failed to update message');
  };

  // Delete message
  const handleDelete = async (messageId) => {
    if (!confirm('Are you sure you want to delete this message?')) {
      return;
    }
    
    const response = await fetch(`http://localhost:8000/api/guestbook/${messageId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      setMessages(messages.filter(msg => msg.id !== messageId));
    } else {
      alert('Failed to delete message');
    }
  };

  return (
    <div className="guestbook">
      <h2>Guest Book</h2>
      
      {/* Add message form */}
      {user && (
        <form onSubmit={handleSubmit}>
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Leave a message..."
          />
          <button type="submit">Post Message</button>
        </form>
      )}
      
      {/* Messages list */}
      {messages.map(msg => (
        <div key={msg.id} className="message">
          <div className="author">
            {msg.name || `${msg.author_first_name} ${msg.author_last_name}`}
            <span className="time">{new Date(msg.created_at).toLocaleDateString()}</span>
          </div>
          <div className="content">{msg.message}</div>
          
          {/* Edit/Delete buttons (only for own messages) */}
          {user && msg.can_edit && (
            <div className="actions">
              <button onClick={() => {
                const newMessage = prompt('Edit message:', msg.message);
                if (newMessage && newMessage !== msg.message) {
                  handleEdit(msg.id, newMessage);
                }
              }}>
                ✏️ Edit
              </button>
              <button onClick={() => handleDelete(msg.id)}>
                🗑️ Delete
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

## Permission Summary

| Action | Permission |
|--------|-----------|
| View all messages | Public (anyone) |
| View single message | Public (anyone) |
| Add message | Authenticated |
| Edit own message | Authenticated + Owner |
| Edit others' messages | ❌ Forbidden (403) |
| Delete own message | Authenticated + Owner |
| Delete others' messages | ❌ Forbidden (403) |

## Error Handling

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```
**Meaning**: Trying to edit/delete someone else's message

### 400 Bad Request
```json
{
  "message": ["This field is required."]
}
```
**Meaning**: Missing required fields (party or message)

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Meaning**: Not logged in (trying to create/edit/delete without auth token)

## Response Fields Explained

- `id`: Unique identifier for the message
- `party`: Party ID this message belongs to
- `party_name`: Name of the party (read-only)
- `author`: User ID of the message author
- `author_username`: Username of the author (read-only)
- `author_first_name`: First name of the author (read-only)
- `author_last_name`: Last name of the author (read-only)
- `name`: Custom display name for the guest book entry (optional)
- `message`: The actual message text
- `created_at`: When the message was created (read-only)
- `updated_at`: When the message was last updated (read-only)
- `can_edit`: Whether the current user can edit/delete this message (read-only, boolean)
