# 🚀 Liara Deployment Guide - Smart Agriculture Dashboard

## 📋 Deploy Full Stack Project on Liara

### **What We're Deploying:**
- ✅ **Backend**: FastAPI with AI Assistant
- ✅ **Frontend**: React/Vite application
- ✅ **Database**: SQLite
- ✅ **AI Features**: Persian/English support
- ✅ **Real-time**: WebSocket connections

## 🚀 **Step 1: Prepare for Liara**

### **1.1 Install Liara CLI**
```bash
# Install Liara CLI
npm install -g @liara/cli

# Login to Liara
liara login
```

### **1.2 Initialize Project**
```bash
# Initialize Liara project
liara init

# Follow the prompts:
# - App name: smart-agriculture-dashboard
# - Platform: Python
# - Build command: pip install -r requirements.txt && cd frontend && npm install && npm run build
# - Start command: python start_server.py
```

## 🔧 **Step 2: Configure Environment Variables**

### **2.1 Set Environment Variables**
```bash
# Set environment variables
liara env set OPENAI_API_KEY "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk"
liara env set OPENAI_API_BASE "https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f"
liara env set OPENAI_MODEL_NAME "openai/gpt-4o-mini"
liara env set PORT "8000"
liara env set HOST "0.0.0.0"
```

## 🚀 **Step 3: Deploy to Liara**

### **3.1 Deploy Application**
```bash
# Deploy to Liara
liara deploy

# Or deploy with specific settings
liara deploy --platform python --build-command "pip install -r requirements.txt && cd frontend && npm install && npm run build" --start-command "python start_server.py"
```

### **3.2 Monitor Deployment**
```bash
# Check deployment status
liara status

# View logs
liara logs

# Check app info
liara info
```

## ✅ **Step 4: Test Your Deployment**

### **4.1 Get Your App URL**
- **Liara will provide**: `https://your-app.liara.run`
- **Test health**: `https://your-app.liara.run/health`
- **Test API docs**: `https://your-app.liara.run/docs`

### **4.2 Test Features**
- ✅ **Dashboard loads**
- ✅ **AI Assistant works**
- ✅ **Real-time data updates**
- ✅ **Persian/English support**
- ✅ **Smart alerts system**

## 🔧 **Step 5: Custom Domain (Optional)**

### **5.1 Add Custom Domain**
```bash
# Add custom domain
liara domain add your-domain.com

# Set up SSL
liara ssl enable
```

## 📊 **Features Working:**

- ✅ **Complete Smart Agriculture Dashboard**
- ✅ **AI Assistant with Persian/English support**
- ✅ **Real-time sensor data**
- ✅ **Smart alerts system**
- ✅ **Multi-tab interface**
- ✅ **Professional UI/UX**
- ✅ **WebSocket real-time updates**

## 🎉 **Success!**

Your Smart Agriculture Dashboard is now live on Liara:
- **URL**: `https://your-app.liara.run`
- **Backend**: FastAPI with AI
- **Frontend**: React with TailwindCSS
- **Database**: SQLite
- **AI**: Persian/English support

---

**🚀 Your complete Smart Agriculture Dashboard is now live on Liara!** 🌱✨
