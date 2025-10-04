# 🚀 Vercel Deployment Guide - Smart Agriculture Dashboard

## 📋 Complete Deployment Instructions

Your project is now ready for Vercel deployment! Follow these steps to deploy your full-stack application.

## 🎯 **What We're Deploying:**

- ✅ **Frontend**: React/Vite application with TailwindCSS
- ✅ **Backend**: FastAPI with AI Assistant (deploy separately on Railway)
- ✅ **Database**: SQLite (or PostgreSQL on Railway)
- ✅ **AI Features**: Persian/English language support
- ✅ **Real-time**: WebSocket connections

## 🚀 **Step 1: Deploy Frontend on Vercel**

### **1.1 Go to Vercel Dashboard**
1. **Visit [vercel.com](https://vercel.com)**
2. **Sign up/Login** with your GitHub account
3. **Click "New Project"**

### **1.2 Import Your Repository**
1. **Select "Import Git Repository"**
2. **Choose your repository**: `alirezagol123/-dashboard.ai`
3. **Click "Import"**

### **1.3 Configure Project Settings**
Vercel will auto-detect your project structure. Configure as follows:

**Project Name**: `smart-agriculture-dashboard`
**Framework Preset**: `Vite`
**Root Directory**: `frontend`
**Build Command**: `npm run build`
**Output Directory**: `dist`
**Install Command**: `npm install`

### **1.4 Environment Variables**
In Vercel dashboard → Settings → Environment Variables, add:

```env
# Backend API URL (you'll get this from Railway)
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_WS_URL=wss://your-backend.railway.app/ws/data

# Optional: Analytics
VITE_APP_NAME=Smart Agriculture Dashboard
VITE_APP_VERSION=1.0.0
```

### **1.5 Deploy**
1. **Click "Deploy"**
2. **Wait for build** (2-3 minutes)
3. **Get your Vercel URL**: `https://your-app.vercel.app`

## 🚀 **Step 2: Deploy Backend on Railway**

### **2.1 Go to Railway Dashboard**
1. **Visit [railway.app](https://railway.app)**
2. **Sign up/Login** with GitHub
3. **Click "New Project"**

### **2.2 Deploy from GitHub**
1. **Select "Deploy from GitHub repo"**
2. **Choose**: `alirezagol123/-dashboard.ai`
3. **Click "Deploy Now"**

### **2.3 Configure Backend Settings**
Railway will auto-detect:
- **Language**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start_server.py`

### **2.4 Set Environment Variables**
In Railway dashboard → Variables tab:

```env
# AI Configuration
OPENAI_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk
OPENAI_API_BASE=https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f
OPENAI_MODEL_NAME=openai/gpt-4o-mini

# Server Configuration
PORT=8000
HOST=0.0.0.0

# Database (Optional - uses SQLite by default)
DATABASE_URL=sqlite:///./smart_dashboard.db
```

### **2.5 Deploy Backend**
1. **Click "Deploy"**
2. **Wait for build** (5-10 minutes)
3. **Get Railway URL**: `https://your-backend.railway.app`

## 🔗 **Step 3: Connect Frontend to Backend**

### **3.1 Update Frontend Environment Variables**
In Vercel dashboard → Settings → Environment Variables:

```env
# Replace with your actual Railway URL
VITE_API_BASE_URL=https://your-actual-backend.railway.app
VITE_WS_URL=wss://your-actual-backend.railway.app/ws/data
```

### **3.2 Redeploy Frontend**
1. **Go to Vercel dashboard**
2. **Click "Redeploy"** on your project
3. **Wait for new deployment**

## ✅ **Step 4: Test Your Deployment**

### **4.1 Test Backend (Railway)**
- **Health Check**: `https://your-backend.railway.app/health`
- **API Docs**: `https://your-backend.railway.app/docs`
- **AI Chat**: `https://your-backend.railway.app/ask`

### **4.2 Test Frontend (Vercel)**
- **Main App**: `https://your-app.vercel.app`
- **Dashboard**: Should load with real-time data
- **AI Assistant**: Should connect to backend
- **Smart Alerts**: Should work with Persian support

## 🎯 **Step 5: Verify All Features**

### **✅ Frontend Features**
- [ ] Dashboard loads correctly
- [ ] All tabs work (Environment, Irrigation, Pest Detection, etc.)
- [ ] AI Assistant sidebar opens
- [ ] Real-time data updates
- [ ] Charts and visualizations work
- [ ] Persian language support

### **✅ Backend Features**
- [ ] API endpoints respond
- [ ] WebSocket connections work
- [ ] AI Assistant processes queries
- [ ] Smart Alerts system works
- [ ] Database operations function
- [ ] Persian/English language detection

### **✅ Integration Features**
- [ ] Frontend connects to backend API
- [ ] WebSocket real-time updates work
- [ ] AI responses appear in frontend
- [ ] Alert management works end-to-end
- [ ] Data flows from backend to frontend

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **Frontend can't connect to backend**:
   - Check `VITE_API_BASE_URL` in Vercel environment variables
   - Verify Railway backend is running
   - Check CORS settings in backend

2. **WebSocket not working**:
   - Check `VITE_WS_URL` in Vercel environment variables
   - Verify WebSocket endpoint is accessible
   - Check browser console for errors

3. **AI Assistant not responding**:
   - Check `OPENAI_API_KEY` in Railway environment variables
   - Verify API key is valid
   - Check Railway logs for errors

4. **Build failures**:
   - Check build logs in Vercel/Railway dashboards
   - Verify all dependencies are installed
   - Check for syntax errors

### **Debug Commands:**
```bash
# Check Railway logs
railway logs

# Check Vercel logs
vercel logs

# Test API endpoints
curl https://your-backend.railway.app/health
curl https://your-backend.railway.app/data/latest
```

## 🎉 **Success!**

Your Smart Agriculture Dashboard should now be live:

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-backend.railway.app`
- **API Docs**: `https://your-backend.railway.app/docs`

## 📊 **Features Working:**

- ✅ **Real-time Dashboard** with live sensor data
- ✅ **AI Assistant** with Persian/English support
- ✅ **Smart Alerts** with natural language creation
- ✅ **Multi-tab Interface** (Environment, Irrigation, Pest Detection, etc.)
- ✅ **WebSocket** real-time updates
- ✅ **Responsive Design** with TailwindCSS
- ✅ **Chart Visualizations** with Chart.js
- ✅ **Professional UI/UX** with modern design

---

**🚀 Your Smart Agriculture Dashboard is now live and ready to use!** 🌱✨

## 🔗 **Quick Links:**

- **Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)
- **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
- **GitHub Repository**: [github.com/alirezagol123/-dashboard.ai](https://github.com/alirezagol123/-dashboard.ai)
