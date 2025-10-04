# 🚀 Liara Setup Guide - Step by Step

## 📋 **Step 1: Create App on Liara Console**

### **1.1 Go to Liara Console**
1. **Visit [console.liara.ir](https://console.liara.ir)**
2. **Sign in** with your account
3. **Click "Create App"** or **"ساخت اپلیکیشن"**

### **1.2 Configure App**
- **App Name**: `smart-agriculture-dashboard`
- **Platform**: **Python**
- **Region**: Choose your preferred region
- **Plan**: Select appropriate plan

### **1.3 Get App ID**
- **Copy the App ID** from the console
- **You'll need this for deployment**

## 🔧 **Step 2: Configure Local Project**

### **2.1 Update liara.json**
```json
{
  "platform": "liara",
  "app": "YOUR_APP_ID_FROM_CONSOLE",
  "build": {
    "command": "pip install -r requirements.txt && cd frontend && npm install && npm run build"
  },
  "start": {
    "command": "python start_server.py"
  }
}
```

### **2.2 Set Environment Variables**
```bash
# Set environment variables
liara env set OPENAI_API_KEY "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk"
liara env set OPENAI_API_BASE "https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f"
liara env set OPENAI_MODEL_NAME "openai/gpt-4o-mini"
liara env set PORT "8000"
liara env set HOST "0.0.0.0"
```

## 🚀 **Step 3: Deploy**

### **3.1 Deploy Application**
```bash
# Deploy to Liara
liara deploy

# Or specify app ID
liara deploy --app YOUR_APP_ID
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

## ✅ **Step 4: Test Your App**

### **4.1 Get Your App URL**
- **Liara will provide**: `https://your-app.liara.run`
- **Test health**: `https://your-app.liara.run/health`
- **Test API docs**: `https://your-app.liara.run/docs`

## 🔧 **Alternative: Deploy via Liara Console**

### **Option 1: Upload via Console**
1. **Go to your app in Liara console**
2. **Click "Deploy"**
3. **Upload your project files**
4. **Set environment variables in console**
5. **Deploy**

### **Option 2: Connect GitHub**
1. **In Liara console, go to your app**
2. **Click "Connect GitHub"**
3. **Select your repository**: `alirezagol123/-dashboard.ai`
4. **Set build and start commands**
5. **Deploy**

## 📊 **Build Commands for Liara:**

### **Build Command:**
```bash
pip install -r requirements.txt && cd frontend && npm install && npm run build
```

### **Start Command:**
```bash
python start_server.py
```

### **Environment Variables:**
```env
OPENAI_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk
OPENAI_API_BASE=https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f
OPENAI_MODEL_NAME=openai/gpt-4o-mini
PORT=8000
HOST=0.0.0.0
```

## 🎉 **Success!**

Your Smart Agriculture Dashboard will be live at:
- **URL**: `https://your-app.liara.run`
- **Features**: Complete full-stack app with AI, real-time data, and Persian support

---

**🚀 Follow these steps to deploy your app on Liara!** 🌱✨

