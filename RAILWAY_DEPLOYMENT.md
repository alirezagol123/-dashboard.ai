# 🚀 Railway Deployment Guide - Full Backend

## 📋 Deploy Everything Except Frontend on Railway

This guide will help you deploy your complete Smart Agriculture Dashboard backend on Railway.

## 🎯 What We're Deploying:

- ✅ **FastAPI Backend** (`app/` folder)
- ✅ **AI Assistant** (LangChain integration)
- ✅ **Smart Alerts** (Persian language support)
- ✅ **Database** (SQLite/PostgreSQL)
- ✅ **WebSocket** (Real-time connections)
- ✅ **All Services** (Alert Manager, Intent Router, etc.)

## 🚀 Step 1: Prepare Your Project

### **1.1 Project Structure**
Your project is already configured with:
- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `runtime.txt` - Python version
- `requirements.txt` - Dependencies

### **1.2 Required Files**
Make sure these files exist:
- ✅ `start_server.py` - Main server file
- ✅ `app/main.py` - FastAPI application
- ✅ `requirements.txt` - Python dependencies
- ✅ `railway.json` - Railway configuration

## 🚀 Step 2: Deploy to Railway

### **2.1 Go to Railway**
1. **Visit [railway.app](https://railway.app)**
2. **Sign up/Login** with GitHub
3. **Click "New Project"**

### **2.2 Connect Repository**
1. **Select "Deploy from GitHub repo"**
2. **Choose your repository**: `alirezagol123/-dashboard.ai`
3. **Click "Deploy Now"**

### **2.3 Configure Settings**
Railway will automatically detect:
- **Language**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start_server.py`

## 🔧 Step 3: Set Environment Variables

### **3.1 Required Environment Variables**
In Railway dashboard → Variables tab, add:

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://ai.liara.ir/api/v1/your_key
PORT=8000
```

### **3.2 Optional Environment Variables**
```
DATABASE_URL=sqlite:///./smart_dashboard.db
PYTHON_VERSION=3.11
LOG_LEVEL=info
```

## 🗄️ Step 4: Database Setup

### **Option A: SQLite (Default)**
- Works out of the box
- Data persists between deployments
- Good for development/testing

### **Option B: Railway Postgres (Production)**
1. **Add Database Service**:
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will provide connection string
2. **Update Environment Variables**:
   - Add `DATABASE_URL` from Railway
3. **Update Database Connection**:
   - Modify `app/db/database.py` to use Postgres

## 🚀 Step 5: Deploy and Test

### **5.1 Deploy**
1. **Click "Deploy"** in Railway dashboard
2. **Wait for build** (5-10 minutes)
3. **Check logs** for any errors

### **5.2 Test Your Deployment**
1. **Get Railway URL**: `https://your-app.railway.app`
2. **Test Health**: `https://your-app.railway.app/health`
3. **Test API Docs**: `https://your-app.railway.app/docs`
4. **Test AI Chat**: `https://your-app.railway.app/ask`

## 🔧 Step 6: Connect Frontend to Backend

### **6.1 Get Railway URL**
- Copy your Railway app URL
- Example: `https://smart-agriculture-dashboard-production.up.railway.app`

### **6.2 Update Frontend (Vercel)**
In Vercel dashboard → Environment Variables:
```
VITE_API_BASE_URL=https://your-app.railway.app
VITE_WS_URL=wss://your-app.railway.app/ws
```

### **6.3 Redeploy Frontend**
```bash
vercel --prod
```

## 🎯 Step 7: Verify Everything Works

### **7.1 Backend Tests**
- ✅ **Health Check**: `https://your-app.railway.app/health`
- ✅ **API Docs**: `https://your-app.railway.app/docs`
- ✅ **AI Chat**: Test Persian/English queries
- ✅ **Smart Alerts**: Create alerts in Persian
- ✅ **WebSocket**: Real-time data updates

### **7.2 Frontend Tests**
- ✅ **Dashboard**: Loads correctly
- ✅ **AI Assistant**: Connects to backend
- ✅ **Smart Alerts**: Shows alerts from backend
- ✅ **Real-time Data**: WebSocket connections work

## 🔧 Step 8: Troubleshooting

### **Common Issues:**

1. **Build Fails**:
   - Check Python version (3.11)
   - Verify all dependencies in `requirements.txt`
   - Check build logs in Railway dashboard

2. **App Won't Start**:
   - Check start command in `Procfile`
   - Verify `start_server.py` exists
   - Check environment variables

3. **Database Issues**:
   - Check `DATABASE_URL` environment variable
   - Verify database service is running
   - Check connection string format

4. **API Not Working**:
   - Verify environment variables
   - Check CORS settings
   - Test individual endpoints

### **Debug Commands:**
```bash
# Check Railway logs
railway logs

# Check service status
railway status

# Connect to service
railway connect
```

## 🎉 Success!

Your Smart Agriculture Dashboard backend should now be live at:
- **Backend**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`
- **Health Check**: `https://your-app.railway.app/health`

## 📊 Features Working:

- ✅ **AI Assistant** with Persian language support
- ✅ **Smart Alerting System** with natural language creation
- ✅ **Real-time WebSocket** connections
- ✅ **Database Operations** (SQLite/Postgres)
- ✅ **All API Endpoints** for frontend
- ✅ **Professional Logging** and monitoring

---

**🚀 Your Smart Agriculture Dashboard backend is now live on Railway!** 🌱✨

## 🔗 Quick Links:

- **Railway Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
- **Your Backend**: `https://your-app.railway.app`
- **GitHub Repository**: `https://github.com/alirezagol123/-dashboard.ai`
