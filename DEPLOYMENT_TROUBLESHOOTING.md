# 🔧 Deployment Troubleshooting Guide

## Common Vercel Deployment Errors & Solutions

### **1. Build Failures**

#### **Error: "Module not found" or "Cannot resolve dependency"**
```bash
# Solution: Update package.json and reinstall
npm install --legacy-peer-deps
```

#### **Error: "Build command failed"**
```bash
# Check if build command is correct in vercel.json
"buildCommand": "npm run build"
```

#### **Error: "Node version incompatible"**
```bash
# Add .nvmrc file to specify Node version
echo "18" > .nvmrc
```

### **2. Environment Variable Issues**

#### **Error: "Environment variable not found"**
```env
# Add these to Vercel Environment Variables:
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_WS_URL=wss://your-backend.railway.app/ws/data
```

### **3. Framework Detection Issues**

#### **Error: "Framework not detected"**
```json
// In vercel.json, ensure:
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

### **4. Path Issues**

#### **Error: "Cannot find module" or "Path not found"**
```bash
# Ensure correct root directory in Vercel:
Root Directory: frontend
```

### **5. Memory/Size Issues**

#### **Error: "Build timeout" or "Memory limit exceeded"**
```json
// In vercel.json, add:
{
  "functions": {
    "app/api/**/*.js": {
      "runtime": "nodejs18.x",
      "maxDuration": 30
    }
  }
}
```

## 🚀 Quick Fixes

### **Fix 1: Update Vercel Configuration**
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev", 
  "installCommand": "npm install",
  "framework": "vite",
  "outputDirectory": "dist",
  "rootDirectory": "frontend"
}
```

### **Fix 2: Add Environment Variables**
```env
NODE_VERSION=18
NPM_VERSION=9
```

### **Fix 3: Update package.json scripts**
```json
{
  "scripts": {
    "build": "vite build",
    "vercel-build": "vite build",
    "preview": "vite preview"
  }
}
```

## 🔍 Debug Steps

### **Step 1: Check Build Locally**
```bash
cd frontend
npm install
npm run build
```

### **Step 2: Check Vercel Logs**
1. Go to Vercel Dashboard
2. Click on your project
3. Go to "Functions" tab
4. Check build logs

### **Step 3: Verify Configuration**
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`
- Framework: `vite`

## 📋 Common Solutions

### **Solution 1: Clean Build**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### **Solution 2: Update Dependencies**
```bash
npm update
npm audit fix
```

### **Solution 3: Check File Structure**
```
frontend/
├── package.json
├── vite.config.js
├── vercel.json
├── src/
└── dist/ (after build)
```

## 🆘 Still Having Issues?

### **Check These Files:**
1. `frontend/package.json` - Dependencies and scripts
2. `frontend/vercel.json` - Vercel configuration
3. `frontend/vite.config.js` - Vite configuration
4. `frontend/src/` - Source code structure

### **Common Error Messages:**
- "Build failed" → Check build command
- "Module not found" → Check dependencies
- "Path not found" → Check root directory
- "Framework not detected" → Check vercel.json
- "Environment variable missing" → Add env vars

---

**Please share the specific error message you're seeing, and I'll provide a targeted solution!** 🚀
