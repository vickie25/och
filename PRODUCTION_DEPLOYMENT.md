# Production Deployment Instructions

## Issue
The frontend is calling `https://cybochengine.africa/api/profiling/status` (Django) instead of `https://cybochengine.africa/ai/api/v1/profiling/status` (FastAPI) because environment variables aren't loaded.

## Root Cause
Next.js bakes `NEXT_PUBLIC_*` environment variables into the build at **build time**, not runtime. The Docker container needs to be rebuilt with the correct `.env.production` file.

## Solution

### On your VPS server:

```bash
# 1. Navigate to project directory
cd /var/www/och

# 2. Update the .env.production file in the frontend
cat > frontend/nextjs_app/.env.production << 'EOF'
NEXT_PUBLIC_DJANGO_API_URL=https://cybochengine.africa/api
NEXT_PUBLIC_FASTAPI_API_URL=https://cybochengine.africa/ai
NEXT_PUBLIC_FRONTEND_URL=https://cybochengine.africa
NODE_ENV=production
DEBUG=false
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_live_YOUR_LIVE_KEY_HERE
NEXT_PUBLIC_SUPABASE_URL=https://sdculxvqvixpiairzukl.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkY3VseHZxdml4cGlhaXJ6dWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MTg4NTUsImV4cCI6MjA3ODk5NDg1NX0.8c2ATXh6692Z3mTG7dsWwivB5uIasrtJeGfj9OLgf98
EOF

# 3. Rebuild the Next.js Docker container
docker-compose build nextjs

# 4. Restart the container
docker-compose up -d nextjs

# 5. Verify environment variables are loaded
docker exec -it ongozacyberhub_nextjs env | grep FASTAPI
# Should show: NEXT_PUBLIC_FASTAPI_API_URL=https://cybochengine.africa/ai

# 6. Check logs
docker logs ongozacyberhub_nextjs --tail 50
```

## Verification

After rebuild, test the profiler:
```bash
# Should return FastAPI response (not Django 404)
curl -H "Authorization: Bearer YOUR_TOKEN" https://cybochengine.africa/api/profiling/status
```

## Alternative: Runtime Environment Variables (if using standalone build)

If you're using Next.js standalone mode, you can set runtime env vars:

```bash
# In docker-compose.yml
services:
  nextjs:
    environment:
      - NEXT_PUBLIC_DJANGO_API_URL=https://cybochengine.africa/api
      - NEXT_PUBLIC_FASTAPI_API_URL=https://cybochengine.africa/ai
```

But this only works if you're NOT using static export. For static builds, you MUST rebuild.
