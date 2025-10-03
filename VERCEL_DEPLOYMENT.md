# 🚀 Vercel Deployment Guide for Smart Agriculture Dashboard

## 📋 Overview

This guide will help you deploy your Smart Agriculture Dashboard to Vercel. Since this is a full-stack application, we'll deploy the frontend to Vercel and the backend to a separate service.

## 🎯 Deployment Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel        │───▶│   Railway/Render│───▶│   Database      │
│   (Frontend)    │    │   (Backend)     │    │   (PostgreSQL)  │
│   React App     │    │   FastAPI       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Step 1: Deploy Frontend to Vercel

### **1.1 Prepare Frontend for Vercel**

1. **Update frontend/vite.config.js**:
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false
  },
  server: {
    port: 3000,
    host: true
  }
})
```

2. **Create frontend/.env.production**:
```env
# Production Environment Variables for Vercel
VITE_API_BASE_URL=https://your-backend-url.railway.app
VITE_WS_URL=wss://your-backend-url.railway.app/ws
VITE_ENABLE_AI_CHAT=true
VITE_ENABLE_ALERTS=true
VITE_ENABLE_WEBSOCKET=true
VITE_DEFAULT_LANGUAGE=fa
VITE_RTL_SUPPORT=true
```

3. **Update frontend/package.json**:
```json
{
  "name": "smart-agriculture-dashboard-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "vercel-build": "vite build"
  }
}
```

### **1.2 Deploy to Vercel**

#### **Option A: Vercel CLI (Recommended)**
```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: smart-agriculture-dashboard
# - Directory: ./
# - Override settings? No
```

#### **Option B: Vercel Dashboard**
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import from GitHub: `alirezagol123/project34`
4. **Root Directory**: `frontend`
5. **Framework Preset**: Vite
6. **Build Command**: `npm run build`
7. **Output Directory**: `dist`
8. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://your-backend-url.railway.app`
   - `VITE_WS_URL`: `wss://your-backend-url.railway.app/ws`

## 🔧 Step 2: Deploy Backend to Railway

### **2.1 Prepare Backend for Railway**

1. **Create Railway configuration**:
```json
// railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python start_server.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

2. **Create requirements.txt** (already exists):
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
langchain==0.0.350
langchain-openai==0.0.2
python-dotenv==1.0.0
websockets==12.0
pandas==2.1.3
numpy==1.25.2
```

3. **Create Procfile**:
```
web: python start_server.py
```

### **2.2 Deploy to Railway**

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `alirezagol123/project34`
5. **Root Directory**: `/` (root)
6. **Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_API_BASE`: Your API base URL
   - `DATABASE_URL`: `postgresql://...` (Railway will provide)
   - `PORT`: `8000`

## 🗄️ Step 3: Set Up Database

### **3.1 Vercel Postgres (Recommended)**
1. In Vercel dashboard → Storage → Create Database
2. Choose "Postgres"
3. Copy connection string
4. Update backend `DATABASE_URL`

### **3.2 Railway Postgres (Alternative)**
1. In Railway dashboard → Add Service → Database → Postgres
2. Copy connection string
3. Update backend `DATABASE_URL`

## 🔗 Step 4: Connect Frontend and Backend

### **4.1 Update Frontend Environment Variables**
In Vercel dashboard → Settings → Environment Variables:
```
VITE_API_BASE_URL=https://your-railway-app.railway.app
VITE_WS_URL=wss://your-railway-app.railway.app/ws
```

### **4.2 Update Backend CORS**
In `app/main.py`, update CORS origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "https://your-vercel-app.vercel.app/",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

## 🚀 Step 5: Deploy and Test

### **5.1 Deploy Backend First**
```bash
# Push changes to GitHub
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### **5.2 Deploy Frontend**
```bash
# Deploy to Vercel
cd frontend
vercel --prod
```

### **5.3 Test Deployment**
1. **Frontend**: Visit your Vercel URL
2. **Backend**: Visit `https://your-railway-app.railway.app/health`
3. **API**: Test `https://your-railway-app.railway.app/docs`

## 🔧 Step 6: Configure Custom Domain (Optional)

### **6.1 Vercel Custom Domain**
1. Vercel dashboard → Settings → Domains
2. Add your domain
3. Configure DNS records

### **6.2 Railway Custom Domain**
1. Railway dashboard → Settings → Domains
2. Add your domain
3. Configure DNS records

## 📊 Step 7: Monitor and Optimize

### **7.1 Vercel Analytics**
- Enable Vercel Analytics
- Monitor performance
- Check error logs

### **7.2 Railway Monitoring**
- Check Railway logs
- Monitor resource usage
- Set up alerts

## 🛠️ Troubleshooting

### **Common Issues:**

1. **CORS Errors**
   - Update CORS origins in backend
   - Check environment variables

2. **WebSocket Connection Failed**
   - Verify WebSocket URL
   - Check Railway WebSocket support

3. **API Calls Failing**
   - Check API base URL
   - Verify backend deployment

4. **Database Connection Issues**
   - Check DATABASE_URL
   - Verify database service

### **Debug Commands:**
```bash
# Check Vercel deployment
vercel logs

# Check Railway deployment
railway logs

# Test API endpoints
curl https://your-railway-app.railway.app/health
```

## 🎯 Final Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway
- [ ] Database connected
- [ ] Environment variables set
- [ ] CORS configured
- [ ] WebSocket working
- [ ] API endpoints responding
- [ ] Persian language support working
- [ ] AI Assistant functional
- [ ] Smart alerts working

## 🎉 Success!

Your Smart Agriculture Dashboard should now be live at:
- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`

---

**🚀 Your Smart Agriculture Dashboard is now deployed and ready for the world!** 🌱✨
