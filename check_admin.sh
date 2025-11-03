#!/bin/bash
# Script to check admin status
# Usage: ./check_admin.sh YOUR_FIREBASE_TOKEN

TOKEN=$1

if [ -z "$TOKEN" ]; then
    echo "Usage: ./check_admin.sh YOUR_FIREBASE_TOKEN"
    echo ""
    echo "To get your token:"
    echo "1. Open browser console on your frontend"
    echo "2. Run: firebase.auth().currentUser.getIdToken().then(t => console.log(t))"
    exit 1
fi

echo "Checking admin status..."
curl -X GET http://localhost:8000/api/check-admin/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python -m json.tool
