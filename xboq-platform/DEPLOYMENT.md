# XBOQ Platform - Deployment Guide

Complete guide to deploy backend + frontend to production.

---

## 🚀 Quick Deploy

### Backend → Render
1. Push code to GitHub
2. Connect Render to repo
3. Add ANTHROPIC_API_KEY
4. Deploy!

### Frontend → Vercel
1. Connect Vercel to repo
2. Set build directory: `frontend`
3. Add API URL environment variable
4. Deploy!

---

## Backend Deployment (Render)

### Step 1: Prepare Repository

```bash
cd xboq-platform
git add .
git commit -m "Production deployment config"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render

### Step 3: Create Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Select `xboq-platform` repo
4. Configure:
   - **Name:** `xboq-backend`
   - **Region:** Oregon (US West)
   - **Branch:** main
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300`
   - **Plan:** Starter ($7/month) or Free

### Step 4: Add Environment Variables

In Render dashboard, add these:

```
FLASK_ENV=production
FLASK_DEBUG=False
ANTHROPIC_API_KEY=sk-ant-...your-key-here
CORS_ORIGINS=https://xboq.vercel.app,https://xboq.ai
```

### Step 5: Deploy

1. Click "Create Web Service"
2. Wait for build (2-3 minutes)
3. Service will be live at: `https://xboq-backend.onrender.com`

### Step 6: Test Endpoints

```bash
# Health check
curl https://xboq-backend.onrender.com/health

# Products
curl https://xboq-backend.onrender.com/api/products

# Trades
curl https://xboq-backend.onrender.com/api/trades
```

---

## Backend Deployment (Railway) - Alternative

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub

### Step 2: Deploy from GitHub

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Link to GitHub repo
railway link

# Add environment variables
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set FLASK_ENV=production

# Deploy
railway up
```

### Step 3: Get URL

```bash
railway domain
# Generates: https://xboq-backend.up.railway.app
```

---

## Frontend Deployment (Vercel)

### Step 1: Update Frontend for Production

Edit `frontend/src/pages/EstimatorPage.jsx` and `frontend/src/App.jsx`:

```javascript
// Add at top of file
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Update fetch calls
fetch(`${API_URL}/api/estimate/manual`, { ... })
fetch(`${API_URL}/api/boq/upload`, { ... })
```

### Step 2: Create Vercel Account

1. Go to https://vercel.com
2. Sign up with GitHub

### Step 3: Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy frontend
cd frontend
vercel

# When prompted:
# Project name: xboq-platform
# Directory: ./ (current directory)
# Framework: Vite
```

### Step 4: Set Environment Variables

In Vercel dashboard:

1. Go to Project Settings → Environment Variables
2. Add:
   ```
   VITE_API_URL=https://xboq-backend.onrender.com
   ```

### Step 5: Redeploy

```bash
vercel --prod
```

Your frontend will be live at: `https://xboq-platform.vercel.app`

---

## Frontend Deployment (Netlify) - Alternative

### Step 1: Build Settings

Create `frontend/netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  VITE_API_URL = "https://xboq-backend.onrender.com"
```

### Step 2: Deploy

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd frontend
netlify deploy --prod
```

---

## Custom Domain Setup

### Backend (Render)

1. Go to Render dashboard → Your service
2. Click "Settings" → "Custom Domain"
3. Add: `api.xboq.ai`
4. Add DNS record:
   ```
   Type: CNAME
   Name: api
   Value: xboq-backend.onrender.com
   ```

### Frontend (Vercel)

1. Go to Vercel dashboard → Your project
2. Click "Settings" → "Domains"
3. Add: `xboq.ai` and `www.xboq.ai`
4. Follow Vercel's DNS instructions

**Update CORS:**
```
CORS_ORIGINS=https://xboq.ai,https://www.xboq.ai
```

---

## Environment Variables Summary

### Backend (.env for local, Render/Railway for production)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Production
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=https://xboq.ai,https://www.xboq.ai

# Optional
MAX_FILE_SIZE_MB=100
UPLOAD_FOLDER=/tmp/uploads
```

### Frontend (Vercel/Netlify environment variables)

```bash
VITE_API_URL=https://api.xboq.ai
```

---

## Database Setup (Future - Week 2)

### PostgreSQL on Render

1. Create new PostgreSQL database
2. Copy connection string
3. Add to backend environment:
   ```
   DATABASE_URL=postgresql://user:pass@host/db
   ```

---

## Monitoring & Logs

### Render Logs

```bash
# View logs in Render dashboard
# Or use CLI
render logs -s xboq-backend -t 100
```

### Vercel Logs

```bash
# View in Vercel dashboard
# Or use CLI
vercel logs xboq-platform
```

---

## Troubleshooting

### Backend won't start

**Check logs for:**
- Missing ANTHROPIC_API_KEY
- Python version mismatch
- Dependency installation errors

**Fix:**
```bash
# Verify requirements.txt
# Ensure runtime.txt specifies Python 3.11.9
# Check Render build logs
```

### CORS errors in frontend

**Problem:** Browser blocks API requests

**Fix:**
```bash
# Backend: Update CORS_ORIGINS
CORS_ORIGINS=https://your-frontend.vercel.app

# Redeploy backend
```

### API calls fail with 404

**Problem:** Wrong API URL

**Fix:**
```javascript
// Frontend: Check VITE_API_URL
console.log(import.meta.env.VITE_API_URL)

// Should be: https://api.xboq.ai (not http://)
```

### File uploads fail

**Problem:** File size or temp directory

**Fix:**
```bash
# Backend: Ensure /tmp/uploads exists
# Render automatically provides /tmp
# Check MAX_FILE_SIZE_MB setting
```

---

## Cost Estimates

### Render (Backend)
- **Free Plan:** 750 hrs/month, sleeps after inactivity
- **Starter Plan:** $7/month, always on, 512MB RAM
- **Professional:** $25/month, 2GB RAM, auto-scaling

### Vercel (Frontend)
- **Hobby:** Free, unlimited bandwidth
- **Pro:** $20/month, team features, analytics

### Railway (Backend Alternative)
- **Free:** $5 credit/month
- **Pay-as-you-go:** ~$5-10/month for starter usage

### Total Monthly Cost
- **Minimum:** $0 (all free tiers)
- **Recommended:** $7-27/month (Render Starter + Vercel Hobby)
- **Production:** $32-52/month (Render Professional + Vercel Pro)

---

## Security Checklist

### Backend
- [ ] ANTHROPIC_API_KEY in environment (not in code)
- [ ] FLASK_DEBUG=False in production
- [ ] CORS configured for production domains only
- [ ] HTTPS enforced (Render does this automatically)
- [ ] File upload size limits set
- [ ] Input validation on all endpoints

### Frontend
- [ ] API URL from environment variable
- [ ] No secrets in frontend code
- [ ] Error messages don't expose internals
- [ ] HTTPS enforced (Vercel does this automatically)

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Environment variables documented
- [ ] CORS configured correctly
- [ ] Error handling tested
- [ ] File uploads tested

### Backend Deployment
- [ ] Code pushed to GitHub
- [ ] Render service created
- [ ] Environment variables set
- [ ] Build successful
- [ ] Health endpoint working
- [ ] API endpoints tested

### Frontend Deployment
- [ ] API URL updated for production
- [ ] Build successful locally
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Deployment successful
- [ ] Site loads correctly
- [ ] API calls working

### Post-Deployment
- [ ] Test all features end-to-end
- [ ] Monitor logs for errors
- [ ] Check performance
- [ ] Set up uptime monitoring (optional)
- [ ] Document deployment URL

---

## CI/CD (Optional - Future)

### GitHub Actions for Auto-Deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        # Render auto-deploys on push to main
      - name: Deploy to Vercel
        run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

---

## Rollback Plan

### Backend Rollback (Render)

1. Go to Render dashboard
2. Click "Deploys"
3. Find previous successful deploy
4. Click "Rollback"

### Frontend Rollback (Vercel)

```bash
vercel rollback
```

Or in Vercel dashboard:
1. Go to "Deployments"
2. Find previous deployment
3. Click "Promote to Production"

---

## Next Steps After Deployment

1. **Test Everything:**
   - BOQ upload
   - Manual estimate
   - Floor plan upload
   - All trades

2. **Monitor for 24 hours:**
   - Check logs
   - Watch for errors
   - Monitor performance

3. **Set up domain (if ready):**
   - Point xboq.ai to Vercel
   - Point api.xboq.ai to Render
   - Update CORS settings

4. **Add analytics (optional):**
   - Google Analytics
   - Plausible
   - PostHog

5. **Set up monitoring:**
   - UptimeRobot (free)
   - Sentry for error tracking
   - LogRocket for session replay

---

## Support

**Backend Issues:**
- Render docs: https://render.com/docs
- Support: support@render.com

**Frontend Issues:**
- Vercel docs: https://vercel.com/docs
- Support: support@vercel.com

**Application Issues:**
- GitHub Issues: https://github.com/yourusername/xboq-platform/issues
- Email: cooperxxjohn@gmail.com

---

**Ready to deploy!** 🚀

Choose your deployment platform and follow the guide above.
