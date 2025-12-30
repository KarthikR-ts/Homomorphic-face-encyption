# 🚀 Railway Deployment Guide

This guide explains how to deploy the Homomorphic Face Encryption application to [Railway](https://railway.app) - a modern cloud platform that doesn't require a credit card for small projects.

## 📋 Prerequisites

1. A [Railway account](https://railway.app) (GitHub sign-in works)
2. Your code pushed to a GitHub repository
3. Basic understanding of environment variables

## 🏗️ Architecture on Railway

The application consists of **3 services**:

```
┌─────────────────────────────────────────────────────────────┐
│                      Railway Project                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Frontend   │  │   Backend    │  │  PostgreSQL  │       │
│  │  (React/Vite)│──│   (Flask)    │──│  (Database)  │       │
│  │   Port: 3000 │  │   Port: 5000 │  │  Port: 5432  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                    Private Network                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step-by-Step Deployment

### Step 1: Create a Railway Project

1. Go to [railway.app](https://railway.app) and log in
2. Click **"New Project"**
3. Select **"Empty Project"**

### Step 2: Add PostgreSQL Database

1. In your project, click **"+ New"**
2. Select **"Database" → "Add PostgreSQL"**
3. Railway automatically provisions the database
4. Note: Railway provides connection variables automatically

### Step 3: Deploy the Backend Service

1. Click **"+ New" → "GitHub Repo"**
2. Select your repository
3. Railway will detect the `Dockerfile.railway` file
4. **Configure the service:**

   Click on the service, go to **Settings**, and set:
   
   - **Root Directory:** `/` (leave as root)
   - **Dockerfile Path:** `Dockerfile.railway`

5. **Add Environment Variables** (in the Variables tab):

   ```env
   # Database (Railway provides these, but link them)
   DB_HOST=${{Postgres.PGHOST}}
   DB_PORT=${{Postgres.PGPORT}}
   DB_USER=${{Postgres.PGUSER}}
   DB_PASSWORD=${{Postgres.PGPASSWORD}}
   DB_NAME=${{Postgres.PGDATABASE}}
   
   # Application Secrets (generate secure values!)
   SECRET_KEY=<generate-a-secure-random-string>
   JWT_SECRET=<generate-another-secure-random-string>
   DB_ENCRYPTION_KEY=<32-character-encryption-key-here>
   
   # Flask Configuration
   FLASK_ENV=production
   PYTHONPATH=/app/src
   
   # CORS (will update after frontend deploys)
   CORS_ORIGINS=https://your-frontend.railway.app
   ```

6. Click **"Deploy"**

### Step 4: Deploy the Frontend Service

1. Click **"+ New" → "GitHub Repo"**
2. Select the **same repository** again
3. **Configure the service:**

   - **Root Directory:** `frontend`
   - **Dockerfile Path:** `Dockerfile.railway`

4. **Add Environment Variables:**

   ```env
   # Point to your backend service
   VITE_API_URL=https://your-backend.railway.app
   ```

5. Click **"Deploy"**

### Step 5: Configure Service Networking

1. **Backend Service:**
   - Go to **Settings → Networking**
   - Click **"Generate Domain"** to get a public URL
   - Copy this URL (e.g., `https://backend-xxxxx.railway.app`)

2. **Frontend Service:**
   - Go to **Settings → Networking**  
   - Click **"Generate Domain"**
   - Copy this URL (e.g., `https://frontend-xxxxx.railway.app`)

3. **Update Environment Variables:**
   - In **Frontend**: Set `VITE_API_URL` to the backend URL
   - In **Backend**: Update `CORS_ORIGINS` to include the frontend URL

4. **Redeploy both services** after updating variables

---

## 🔧 Environment Variables Reference

### Backend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | Database host | Use Railway's `${{Postgres.PGHOST}}` |
| `DB_PORT` | Database port | Use `${{Postgres.PGPORT}}` |
| `DB_USER` | Database user | Use `${{Postgres.PGUSER}}` |
| `DB_PASSWORD` | Database password | Use `${{Postgres.PGPASSWORD}}` |
| `DB_NAME` | Database name | Use `${{Postgres.PGDATABASE}}` |
| `SECRET_KEY` | Flask secret key | Generate a secure random string |
| `JWT_SECRET` | JWT signing secret | Generate a secure random string |
| `DB_ENCRYPTION_KEY` | Database encryption key | 32+ character string |
| `FLASK_ENV` | Flask environment | `production` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://frontend.railway.app` |
| `REDIS_URL` | Redis connection (optional) | Leave empty if not using Redis |

### Frontend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://backend.railway.app` |
| `PORT` | Server port (auto-set by Railway) | Auto-configured |

---

## 🔐 Generating Secure Secrets

Use these commands to generate secure secrets:

```bash
# For SECRET_KEY and JWT_SECRET (on Linux/Mac)
openssl rand -hex 32

# For Windows PowerShell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }) -as [byte[]])

# For DB_ENCRYPTION_KEY (must be exactly 32 characters)
openssl rand -hex 16
```

Or use an online generator: [RandomKeygen](https://randomkeygen.com/)

---

## 🐛 Troubleshooting

### Backend won't start

1. **Check logs:** Click on the service → View Logs
2. **Verify environment variables:** Ensure all required vars are set
3. **Database connection:** Make sure the Postgres service is running

### Frontend can't connect to backend

1. **CORS issue:** Verify `CORS_ORIGINS` includes the frontend URL
2. **Wrong API URL:** Check `VITE_API_URL` is correct
3. **Redeploy:** After changing env vars, redeploy the service

### Database connection errors

1. **Use Railway variables:** Instead of hardcoding, use `${{Postgres.VARIABLE}}`
2. **Check service linking:** Ensure services can communicate

### Build failures

1. **Check Dockerfile:** Ensure `Dockerfile.railway` exists
2. **Root directory:** Verify the correct root directory is set
3. **Dependencies:** Check if all packages are in requirements.txt

---

## 💡 Tips for Railway

1. **Service Variables:** Use `${{ServiceName.VAR}}` syntax to reference other services
2. **Private Networking:** Services can communicate via internal hostnames
3. **Automatic HTTPS:** Railway provides SSL certificates automatically
4. **Deploy Triggers:** Connect to GitHub for automatic deployments on push
5. **Resource Limits:** Monitor usage to stay within free tier

---

## 📊 Resource Estimates

| Service | Memory | CPU | Notes |
|---------|--------|-----|-------|
| Backend (Flask) | ~512MB-1GB | Medium | ML models load here |
| Frontend (Static) | ~128MB | Low | Just serves static files |
| PostgreSQL | ~256MB | Low | Database storage |

**Free Tier:** Railway offers $5/month credit for free accounts, which is usually sufficient for development and small projects.

---

## 🔄 Continuous Deployment

Railway automatically deploys when you push to your connected GitHub branch:

1. Push code to GitHub
2. Railway detects the change
3. Builds and deploys automatically
4. Zero-downtime deployments

To deploy manually:
1. Go to your service
2. Click **"Deploy"** → **"Trigger Deploy"**

---

## 📞 Support

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- [GitHub Issues](https://github.com/your-repo/issues)

Happy deploying! 🎉
