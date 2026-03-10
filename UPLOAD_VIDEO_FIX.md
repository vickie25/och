# Video Upload Fix

## Issue
Getting "Failed to upload video" error when uploading video files.

## Root Cause
The URL construction in the XMLHttpRequest is incorrect. The `NEXT_PUBLIC_DJANGO_API_URL` environment variable likely already includes `/api`, so we're creating a malformed URL.

## Solution

In the file: `frontend/nextjs_app/app/dashboard/director/modules/page.tsx`

Find both occurrences of this line (in AddLessonForm and EditLessonForm):
```typescript
xhr.open('POST', `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/v1/curriculum/lessons/upload-video/`)
```

Replace with:
```typescript
const baseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL?.endsWith('/api') 
  ? process.env.NEXT_PUBLIC_DJANGO_API_URL.replace(/\/api$/, '')
  : process.env.NEXT_PUBLIC_DJANGO_API_URL;
xhr.open('POST', `${baseUrl}/api/v1/curriculum/lessons/upload-video/`)
```

## Manual Fix Instructions

1. Open: `frontend/nextjs_app/app/dashboard/director/modules/page.tsx`

2. Search for: `xhr.open('POST',` (there are 2 occurrences)

3. In the **AddLessonForm** function (around line 1050), replace:
```typescript
xhr.open('POST', `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/v1/curriculum/lessons/upload-video/`)
```
with:
```typescript
const baseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL?.endsWith('/api') 
  ? process.env.NEXT_PUBLIC_DJANGO_API_URL.replace(/\/api$/, '')
  : process.env.NEXT_PUBLIC_DJANGO_API_URL;
xhr.open('POST', `${baseUrl}/api/v1/curriculum/lessons/upload-video/`)
```

4. In the **EditLessonForm** function (around line 1350), make the same replacement

5. Save the file

## Alternative: Check Environment Variable

Check your `.env.local` file. If `NEXT_PUBLIC_DJANGO_API_URL` is set to something like:
- `http://localhost:8000/api` - This is causing the issue

Change it to:
- `http://localhost:8000` - Without the `/api` suffix

Then the current code will work without modification.
