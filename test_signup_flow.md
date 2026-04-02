# Email Verification Flow Test

## 1. Signup
```bash
curl -X POST http://localhost:3000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","first_name":"Test","last_name":"User","role":"student"}'
```

**Expected Response:**
```json
{
  "detail": "Registration successful. Please check your email to activate your account.",
  "user_id": 123,
  "message": "Registration successful. Please check your email to activate your account."
}
```

**Frontend Redirect:** `/auth/verify-email?registered=true`

## 2. Email Verification
Get the verification token from Django admin or logs, then visit:
```
http://localhost:3000/auth/verify-email?token=TOKEN_HERE
```

**Expected Result:** Email verified successfully

## 3. Login
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

**Expected Response:**
```json
{
  "user": {
    "id": "123",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "account_status": "active"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

## Flow Summary
1. **Signup** → User created with `pending_verification` status
2. **Redirect** → User sent to `/auth/verify-email?registered=true`
3. **Email** → Verification email sent with token link
4. **Verification** → User clicks link, account activated
5. **Login** → User can now login successfully

## Common Issues
- **"Authentication Failed"**: User trying to login before email verification
- **"Invalid token"**: Token expired or already used
- **"User not found"**: Wrong email address during verification

## Testing Commands
```bash
# Get verification token for user
cd /Users/airm1/Projects/och/backend/django_app
python3 manage.py shell -c "
from users.models import User
u = User.objects.get(email='test@example.com')
token = u.generate_verification_token()
print(f'Token: {token}')
print(f'URL: http://localhost:3000/auth/verify-email?token={token}')
"
```
