#!/usr/bin/env python3
"""
Quick script to check admin status
Usage: python check_admin.py YOUR_FIREBASE_TOKEN
"""

import sys
import requests
import json

if len(sys.argv) < 2:
    print("Usage: python check_admin.py YOUR_FIREBASE_TOKEN")
    print("\nTo get your Firebase token:")
    print("1. Open browser console on your frontend")
    print("2. Run: firebase.auth().currentUser.getIdToken().then(t => console.log(t))")
    sys.exit(1)

token = sys.argv[1]
url = "http://localhost:8000/api/check-admin/"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    
    print("\n" + "="*50)
    print("ADMIN STATUS CHECK")
    print("="*50)
    print(json.dumps(data, indent=2))
    print("="*50)
    
    if data.get('is_admin'):
        print("✅ You ARE an admin!")
    else:
        print("❌ You are NOT an admin")
        print("\nIf you expected to be admin:")
        print("1. Make sure you logged out and back in")
        print("2. Check your Django user with: python manage.py shell")
        print("3. Verify: User.objects.get(username='your-firebase-uid').is_staff")
        
except requests.exceptions.ConnectionError:
    print("❌ Error: Could not connect to http://localhost:8000")
    print("Make sure your Django server is running!")
except Exception as e:
    print(f"❌ Error: {e}")
