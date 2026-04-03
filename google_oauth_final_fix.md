# Google OAuth Final Fix Guide

## Issue Analysis Summary

After extensive testing, I've determined that:

✅ **Django Backend**: Working correctly
✅ **Google OAuth Configuration**: Client credentials are valid
✅ **API Endpoints**: Both initiate and callback work correctly
✅ **Frontend Implementation**: Correctly calls backend services

The "unauthorized_client" error is likely due to one of these environmental issues:

## 🔧 **Solution Steps**

### Step 1: Verify Google OAuth Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to: **APIs & Services > Credentials**
3. Find your OAuth 2.0 Client ID: `[REDACTED_FOR_SECURITY]`
4. Click **Edit** or **Configure**
5. Under **Authorized redirect URIs**, ensure you have EXACTLY:
   ```
   http://localhost:3000/auth/google/callback
   ```
6. **Important**: The URI must match EXACTLY (including http://, localhost, port 3000, and the full path)
7. Save the configuration
8. Wait 5-10 minutes for changes to propagate

### Step 2: Clear Browser Cache and Cookies

1. Clear all browser cookies for localhost:3000
2. Clear browser cache
3. Close and reopen browser
4. Try the OAuth flow again

### Step 3: Test the Complete Flow

1. Visit: `http://localhost:3000/login/student`
2. Click "Continue with Google"
3. You should be redirected to Google
4. Authenticate with your Google account
5. You should be redirected back to: `http://localhost:3000/auth/google/callback`
6. The callback should process and redirect you to the dashboard

### Step 4: If Still Failing - Check These

#### A. Multiple Client IDs
Ensure you're using the correct client ID:
```
[REDACTED_CLIENT_ID]
```

#### B. Environment Variables
Verify these are set in `backend/django_app/.env`:
```bash
GOOGLE_CLIENT_ID=[REDACTED_FOR_SECURITY]
GOOGLE_CLIENT_SECRET=[REDACTED_FOR_SECURITY]
FRONTEND_URL=http://localhost:3000
```

#### C. Frontend URL Configuration
Ensure the frontend is running on port 3000:
```bash
# Check if Next.js is running on port 3000
curl -s http://localhost:3000 | head -1
```

## 🔍 **Debug Commands**

### Test Backend Directly:
```bash
# Test initiate
curl -s "http://localhost/api/v1/auth/google/initiate?role=student"

# Test callback (should give "invalid_grant" for fake code)
curl -s -X POST "http://localhost/api/v1/auth/google/callback" \
  -H "Content-Type: application/json" \
  -d '{"code":"fake","state":"test"}'
```

### Test Frontend Integration:
```bash
# Check if frontend is accessible
curl -s http://localhost:3000/login/student | grep -o "Continue with Google"
```

## 📋 **Verification Checklist**

- [ ] Google OAuth Console has correct redirect URI
- [ ] Client ID matches exactly
- [ ] Client secret is correct
- [ ] Frontend running on port 3000
- [ ] Backend API accessible at http://localhost/api/v1/*
- [ ] Browser cache cleared
- [ ] Waited 5+ minutes after Google Console changes

## 🚀 **Expected Working Flow**

1. **Initiate**: Frontend → Django → Google (auth_url)
2. **Authenticate**: User authenticates with Google
3. **Callback**: Google → Frontend callback page → Django backend
4. **Complete**: Django processes tokens → User logged in → Redirect to dashboard

## 🆘 **If Still Not Working**

If you've tried all the above and still get "unauthorized_client":

1. **Create a new OAuth client** in Google Console
2. **Update environment variables** with new client ID/secret
3. **Re-register the redirect URI** for the new client
4. **Restart Docker containers**:
   ```bash
   docker-compose restart django nextjs
   ```

## 📞 **Support**

The backend code is working correctly - the issue is purely configuration-related in the Google OAuth Console. The error "unauthorized_client" specifically means Google doesn't recognize the redirect URI or client credentials being used.
