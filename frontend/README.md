# 🎨 Smart Agriculture Dashboard - Frontend

## Overview

The frontend of the Smart Agriculture Dashboard is a modern React.js application built with Vite, providing a comprehensive interface for agricultural monitoring, AI-powered analytics, and smart alerting. It features complete Persian language support, real-time data visualization, and an intuitive user experience.

## 🏗️ Architecture

### **Frontend Architecture**

```
┌─────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Components  │───▶│   API Services  │───▶│   FastAPI       │
│   (Dashboard,       │    │   (api.js,      │    │   Backend       │
│    AlertsManager,   │    │    ws.js)       │    │   + WebSocket   │
│    LangChainChat)   │    │                 │    │   + AI          │
└─────────────────────┘    └─────────────────┘    └─────────────────┘
                                      │                       │
                                      ▼                       ▼
                           ┌─────────────────┐    ┌─────────────────┐
                           │   Real-time     │◀───│   WebSocket     │
                           │   Updates       │    │   Streaming     │
                           │   + Alerts      │    │   + Data        │
                           └─────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

### **Core Technologies**
- **Framework**: React.js 18.2.0
- **Build Tool**: Vite 4.5.0
- **Styling**: TailwindCSS 3.3.5
- **Icons**: Lucide React 0.294.0
- **Charts**: Chart.js 4.5.0, Recharts 2.8.0
- **HTTP Client**: Axios 1.6.0
- **WebSocket**: Native WebSocket API

### **Development Tools**
- **Linting**: ESLint 8.53.0
- **PostCSS**: 8.4.31
- **Autoprefixer**: 10.4.16
- **TypeScript**: @types/react, @types/react-dom

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/              # React Components
│   │   ├── AlertsManager.jsx    # Smart alerts UI with Persian support
│   │   ├── Chart.jsx            # Chart visualization component
│   │   ├── DataVisualizer.jsx   # Data visualization wrapper
│   │   ├── LangChainChat.jsx    # AI chat interface
│   │   ├── QueryAssistant.jsx   # Query assistant component
│   │   └── StatsCard.jsx        # Statistics display card
│   ├── pages/
│   │   └── Dashboard.jsx        # Main dashboard page
│   ├── services/                # API Services
│   │   ├── api.js              # REST API client
│   │   └── ws.js               # WebSocket client
│   ├── App.jsx                 # Main application component
│   ├── index.css               # Global styles
│   └── main.jsx                # Application entry point
├── public/                     # Static assets
├── dist/                       # Build output
├── package.json                # Dependencies and scripts
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # TailwindCSS configuration
└── postcss.config.js          # PostCSS configuration
```

## 🎯 Key Features

### ✅ **Comprehensive Dashboard**

#### **Multi-Tab Interface**
- **Environmental**: Temperature, humidity, pressure, light, CO2 monitoring
- **Irrigation**: Soil moisture, water usage, irrigation management
- **Pest Detection**: Pest monitoring, disease risk assessment
- **Fertilization**: Soil pH, N-P-K levels, nutrient management
- **Harvest**: Plant growth, fruit development, yield prediction
- **Marketplace**: Crop prices, demand/supply analysis
- **Analytics**: Performance metrics, efficiency analysis
- **AI Assist**: LangChain-powered chat interface
- **Alerts**: Smart alerting system with Persian support

#### **Real-time Data Visualization**
- Live sensor data updates via WebSocket
- Interactive charts and graphs
- Statistics cards with key metrics
- Real-time alert notifications
- Persian language support throughout

### ✅ **AI Assistant Integration**

#### **LangChainChat Component**
- Natural language query processing
- Persian and English language support
- Real-time streaming responses
- Conversation history management
- Context-aware responses

#### **Features**
- **Language Detection**: Automatic Persian/English detection
- **Streaming Responses**: Real-time token-by-token responses
- **Session Management**: User session tracking
- **Context Awareness**: Feature-specific responses
- **Error Handling**: Graceful error recovery

### ✅ **Smart Alerting System**

#### **AlertsManager Component**
- Natural language alert creation
- Real-time alert monitoring
- Persian interface with RTL support
- Recommended actions with Act/Pass options
- Priority-based alert management

#### **Alert Features**
- **Natural Language Creation**: "وقتی دما بیشتر از 25 شد هشدار بده"
- **Real-time Monitoring**: Continuous sensor data checking
- **Persian Responses**: Complete Persian interface
- **Action Management**: Act/Pass options for each alert
- **Sound Alerts**: Professional alert sounds
- **Browser Notifications**: Desktop notifications

### ✅ **Persian Language Support**

#### **Complete Localization**
- **UI Text**: All interface text in Persian
- **RTL Support**: Right-to-left text layout
- **Cultural Adaptation**: Iranian agricultural terminology
- **Date/Time**: Persian calendar and time formatting
- **Numbers**: Persian number formatting

#### **AI Integration**
- **Persian Queries**: Natural language in Persian
- **Persian Responses**: AI responses in Persian
- **Translation**: Automatic Persian/English translation
- **Context Awareness**: Persian agricultural context

## 🚀 Getting Started

### **Prerequisites**
- Node.js 16+
- npm or yarn
- Backend server running on port 8000

### **Installation**

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Access Application**
   - Open http://localhost:3000
   - Ensure backend is running on port 8000

### **Build for Production**

1. **Build Application**
   ```bash
   npm run build
   ```

2. **Preview Production Build**
   ```bash
   npm run preview
   ```

## 🔧 Configuration

### **Environment Variables**
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Feature Flags
VITE_ENABLE_AI_CHAT=true
VITE_ENABLE_ALERTS=true
VITE_ENABLE_WEBSOCKET=true

# Persian Language Support
VITE_DEFAULT_LANGUAGE=fa
VITE_RTL_SUPPORT=true
```

### **Vite Configuration**
```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### **TailwindCSS Configuration**
```javascript
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        'persian': ['Vazir', 'Tahoma', 'sans-serif']
      },
      direction: {
        'rtl': 'rtl'
      }
    }
  },
  plugins: []
}
```

## 📊 Components Overview

### **Dashboard.jsx** - Main Dashboard
- **Purpose**: Central dashboard with tab navigation
- **Features**: 
  - Multi-tab interface
  - WebSocket connection management
  - Session management
  - Persian language support
  - Real-time data updates

### **AlertsManager.jsx** - Smart Alerts
- **Purpose**: Alert creation, management, and monitoring
- **Features**:
  - Natural language alert creation
  - Real-time alert monitoring
  - Persian interface with RTL support
  - Act/Pass action options
  - Sound alerts and notifications

### **LangChainChat.jsx** - AI Chat
- **Purpose**: AI-powered chat interface
- **Features**:
  - Natural language query processing
  - Streaming responses
  - Persian/English support
  - Conversation history
  - Context-aware responses

### **Chart.jsx** - Data Visualization
- **Purpose**: Chart and graph components
- **Features**:
  - Multiple chart types (line, bar, pie)
  - Real-time data updates
  - Interactive charts
  - Persian labels and formatting

### **DataVisualizer.jsx** - Data Wrapper
- **Purpose**: Data visualization wrapper
- **Features**:
  - Data processing and formatting
  - Chart type selection
  - Error handling
  - Loading states

### **StatsCard.jsx** - Statistics Display
- **Purpose**: Statistics and metrics display
- **Features**:
  - Key metrics display
  - Real-time updates
  - Persian formatting
  - Visual indicators

## 🔌 API Integration

### **REST API Client** (`services/api.js`)
```javascript
// API endpoints
const API_BASE = 'http://localhost:8000';

// Data endpoints
export const getLatestData = (limit = 20) => 
  fetch(`${API_BASE}/data/latest?limit=${limit}`);

export const getDataStats = () => 
  fetch(`${API_BASE}/data/stats`);

// AI endpoints
export const askAI = (query, featureContext) => 
  fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, feature_context: featureContext })
  });

// Alert endpoints
export const getAlerts = () => 
  fetch(`${API_BASE}/api/alerts`);

export const createAlert = (query) => 
  fetch(`${API_BASE}/api/alerts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
```

### **WebSocket Client** (`services/ws.js`)
```javascript
// WebSocket connection
class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    this.socket = new WebSocket(this.url);
    
    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.socket.onclose = () => {
      this.handleReconnect();
    };
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, 1000 * this.reconnectAttempts);
    }
  }
}
```

## 🎨 Styling & UI

### **TailwindCSS Classes**
```css
/* Persian text styling */
.persian-text {
  @apply font-persian text-right;
}

/* RTL layout */
.rtl-layout {
  @apply direction-rtl;
}

/* Alert cards */
.alert-card {
  @apply bg-white border border-gray-200 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300 border-l-4 border-l-red-500;
}

/* Persian buttons */
.persian-button {
  @apply px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium;
}
```

### **Responsive Design**
- **Mobile**: Optimized for mobile devices
- **Tablet**: Responsive grid layouts
- **Desktop**: Full-featured interface
- **RTL Support**: Right-to-left text layout

## 🧪 Testing

### **Component Testing**
```bash
# Run component tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### **Integration Testing**
```bash
# Test API integration
npm run test:integration

# Test WebSocket connection
npm run test:websocket

# Test Persian language support
npm run test:persian
```

### **Manual Testing**
1. **Language Support**: Test Persian/English queries
2. **Real-time Updates**: Verify WebSocket connection
3. **Alert System**: Create and monitor alerts
4. **AI Chat**: Test natural language processing
5. **Responsive Design**: Test on different screen sizes

## 🚀 Deployment

### **Build Process**
```bash
# Install dependencies
npm install

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Production Configuration**
```javascript
// vite.config.js for production
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['chart.js', 'recharts'],
          ui: ['lucide-react', 'tailwindcss']
        }
      }
    }
  }
})
```

### **Docker Deployment**
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🛠️ Troubleshooting

### **Common Issues**

1. **WebSocket Connection Failed**
   - Check if backend is running on port 8000
   - Verify WebSocket endpoint accessibility
   - Check firewall settings

2. **API Requests Failing**
   - Verify API base URL configuration
   - Check CORS settings on backend
   - Monitor network requests in browser dev tools

3. **Persian Text Not Displaying**
   - Check font configuration
   - Verify RTL support
   - Check character encoding

4. **Build Errors**
   - Clear node_modules and reinstall
   - Check for dependency conflicts
   - Verify Node.js version compatibility

5. **Performance Issues**
   - Check bundle size
   - Optimize images and assets
   - Monitor memory usage
   - Use React DevTools for profiling

### **Debug Tools**
```bash
# Check bundle size
npm run build -- --analyze

# Check for unused dependencies
npm run audit

# Check for security vulnerabilities
npm audit

# Check for outdated packages
npm outdated
```

## 📈 Performance Optimization

### **Code Splitting**
- Lazy loading for components
- Dynamic imports for heavy libraries
- Route-based code splitting

### **Asset Optimization**
- Image optimization
- Font loading optimization
- CSS purging with TailwindCSS

### **Caching Strategy**
- Service worker for offline support
- API response caching
- Static asset caching

## 🔮 Future Enhancements

### **Planned Features**
1. **PWA Support**: Progressive Web App capabilities
2. **Offline Support**: Offline data access and sync
3. **Advanced Charts**: More chart types and interactions
4. **Mobile App**: React Native mobile application
5. **Real-time Collaboration**: Multi-user features

### **Performance Improvements**
1. **Virtual Scrolling**: For large data sets
2. **Memoization**: React.memo and useMemo optimization
3. **Bundle Optimization**: Further code splitting
4. **CDN Integration**: Static asset delivery

---

**🎨 The Smart Agriculture Dashboard Frontend provides a comprehensive, Persian-language interface for agricultural monitoring, AI-powered analytics, and smart alerting, built with modern React.js and optimized for performance and user experience.**