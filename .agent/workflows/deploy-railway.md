---
description: Deploy the Homomorphic Face Encryption application to Railway (No Credit Card Required)
---

# Deploy to Railway (FREE - No Credit Card)

## ⚡ Quick Facts
- **Cost:** FREE ($5/month credit, no credit card needed)
- **Time:** ~15 minutes
- **Difficulty:** Easy
- **Services:** Backend, Frontend, PostgreSQL all included

---

## 📋 Prerequisites

1. **GitHub Account** (free)
2. **Railway Account** (free, sign up with GitHub)
3. **Your code pushed to GitHub**

---

## 🚀 Deployment Steps

### Step 1: Push Code to GitHub

// turbo
```powershell
# Navigate to project
cd "z:\DTL_HACKATHON\Homomorphic-face-encyption"

# Check git status
git status

# Add all files
git add .

# Commit
git commit -m "Add Railway deployment configuration"

# Push to GitHub (assuming origin is already set)
git push origin main
```

### Step 2: Sign Up for Railway

1. Go to https://railway.app
2. Click "Login" → "Login with GitHub"
3. Authorize Railway to access your GitHub

**✅ You now have $5 free credit per month!**

---

### Step 3: Create New Project

1. **Click "New Project"**
2. **Select "Empty Project"** (we'll add services manually for better control)

---

### Step 4: Add PostgreSQL Database

1. Click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway provisions it automatically
3. The connection details are auto-configured as internal variables

---

### Step 5: Deploy the Backend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. **Choose your repository:** `Homomorphic-face-encyption`
3. In **Settings** tab:
   - **Root Directory:** Leave empty (uses project root)
   - **Build Command:** Dockerfile-based (auto-detected)
   - If prompted, select `Dockerfile.railway`

4. **Add Environment Variables** (Variables tab):

```env
# Database (use Railway's reference variables)
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}
DB_USER=${{Postgres.PGUSER}}
DB_PASSWORD=${{Postgres.PGPASSWORD}}
DB_NAME=${{Postgres.PGDATABASE}}

# App Config (GENERATE SECURE VALUES!)
SECRET_KEY=replace-with-32-character-secure-random-string
JWT_SECRET=replace-with-another-secure-random-string
DB_ENCRYPTION_KEY=32-character-encryption-key-here

# Flask Configuration
FLASK_ENV=production
PYTHONPATH=/app/src

# CORS (update after frontend deploys)
CORS_ORIGINS=https://your-frontend.railway.app
```

5. **Generate Domain:**
   - Go to **Settings → Networking**
   - Click **"Generate Domain"**
   - Copy the URL (e.g., `https://backend-xxxx.railway.app`)

6. **Deploy** - Railway auto-deploys, or click "Deploy Now"

---

### Step 6: Deploy the Frontend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. **Choose the SAME repository** again
3. In **Settings** tab:
   - **Root Directory:** `frontend`
   - Railway will detect `Dockerfile.railway` in the frontend folder

4. **Add Environment Variables:**

```env
# Point to your backend service URL from Step 5
VITE_API_URL=https://your-backend-xxxx.railway.app
```

5. **Generate Domain:**
   - Go to **Settings → Networking**
   - Click **"Generate Domain"**
   - Copy the URL (e.g., `https://frontend-xxxx.railway.app`)

---

### Step 7: Update Backend CORS

1. Go back to your **Backend service**
2. Click **Variables** tab
3. Update `CORS_ORIGINS` to include your frontend URL:
   ```
   CORS_ORIGINS=https://your-frontend-xxxx.railway.app
   ```
4. Railway will automatically redeploy

---

## 🔐 Generate Secure Secrets

Run these commands to generate secure random strings:

// turbo
```powershell
# Generate SECRET_KEY (PowerShell)
[guid]::NewGuid().ToString().Replace("-","") + [guid]::NewGuid().ToString().Replace("-","")

# Generate JWT_SECRET
[Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Maximum 256) }))

# Generate DB_ENCRYPTION_KEY (exactly 32 chars)
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

---

## ✅ Post-Deployment Checklist

1. **Test Backend Health:**
   ```
   https://your-backend.railway.app/health
   ```

2. **Test API Root:**
   ```
   https://your-backend.railway.app/
   ```

3. **Test Frontend:**
   - Open your frontend URL
   - Should display the login/consent interface

---

## 📁 Railway Configuration Files

These files have been created in your project:

### Backend (`Dockerfile.railway`)
- Optimized Python 3.11 image
- Includes all ML dependencies
- Runs with gunicorn

### Frontend (`frontend/Dockerfile.railway`)
- Multi-stage Node.js build
- Serves static files with `serve`
- Respects Railway's PORT variable

### Procfiles (alternative to Dockerfiles)
- `Procfile` - Backend process command
- `frontend/Procfile` - Frontend process command

---

## 🐛 Troubleshooting

### Build Fails
- Click service → **Deployments** → **View Logs**
- Check if all dependencies are in `requirements.txt`
- Verify Dockerfile syntax

### Database Connection Error
- Ensure PostgreSQL service is in the same project
- Check environment variables use `${{Postgres.VARIABLE}}` syntax
- Verify service is running (check for green status)

### CORS Errors
- Update `CORS_ORIGINS` to include exact frontend URL
- Include `https://` prefix
- Redeploy backend after changing

### Frontend Can't Connect to Backend
- Verify `VITE_API_URL` is set correctly
- Ensure backend is deployed and has a public domain
- Check browser console for specific errors

### App Shows "Service Unavailable"
- Check deployment logs for errors
- Verify PORT is being respected
- May need to wait for cold start (first request is slower)

---

## 💰 Resource Usage

| Service | Estimated Cost |
|---------|---------------|
| Backend (Flask + ML) | ~$2-3/month |
| Frontend (Static) | ~$0.50/month |
| PostgreSQL | ~$1/month |
| **Total** | **~$4/month** (within free tier!) |

---

## 🔄 Automatic Deployments

Railway automatically deploys when you push to GitHub:

1. Make code changes
2. `git push origin main`
3. Railway detects changes
4. Builds and deploys automatically

---

## 📚 Additional Resources

- [Full Railway Documentation](RAILWAY_DEPLOYMENT.md) (in project root)
- [Railway Official Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)

---

**Last Updated:** 2025-12-30
**Status:** ✅ Ready for deployment
