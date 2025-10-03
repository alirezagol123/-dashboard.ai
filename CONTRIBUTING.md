# Contributing to Smart Agriculture Dashboard

Thank you for your interest in contributing to the Smart Agriculture Dashboard! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git
- GitHub account

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/smart-agriculture-dashboard.git
   cd smart-agriculture-dashboard
   ```

2. **Install Dependencies**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install Node.js dependencies
   npm install
   cd frontend && npm install
   ```

3. **Set Up Environment**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Edit .env with your configuration
   # OPENAI_API_KEY=your-api-key
   # OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
   ```

4. **Start Development**
   ```bash
   # Start backend
   python start_server.py
   
   # Start frontend (in another terminal)
   cd frontend && npm run dev
   ```

## 📝 How to Contribute

### 1. **Bug Reports**
- Use the GitHub issue tracker
- Include steps to reproduce
- Provide system information
- Include error messages and logs

### 2. **Feature Requests**
- Use the GitHub issue tracker
- Describe the feature clearly
- Explain the use case
- Consider implementation complexity

### 3. **Code Contributions**

#### **Pull Request Process**
1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Your Changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation

3. **Commit Your Changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

4. **Push to Your Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Create a Pull Request**
   - Use the PR template
   - Describe your changes
   - Link related issues

## 🎯 Development Guidelines

### **Code Style**

#### **Python**
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Use meaningful variable names

#### **JavaScript/React**
- Use ESLint configuration
- Follow React best practices
- Use functional components with hooks
- Write meaningful component names

### **Commit Messages**
Use clear, descriptive commit messages:
```
feat: add smart alerting system
fix: resolve WebSocket connection issues
docs: update API documentation
style: format code according to standards
refactor: improve query processing logic
test: add unit tests for alert manager
```

### **Testing**
- Write tests for new features
- Ensure existing tests pass
- Test both Persian and English functionality
- Test real-time features

## 🏗️ Project Structure

### **Backend (Python/FastAPI)**
```
app/
├── db/                 # Database configuration
├── models/             # SQLAlchemy models
├── services/           # Business logic
│   ├── ai_assistant.py
│   ├── alert_manager.py
│   ├── unified_semantic_service.py
│   └── ...
└── main.py            # FastAPI application
```

### **Frontend (React.js)**
```
frontend/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   ├── services/      # API services
│   └── ...
└── package.json
```

## 🌐 Internationalization

### **Persian Language Support**
- All UI text should be in Persian
- Use RTL layout for Persian content
- Test with Persian agricultural terminology
- Ensure proper character encoding

### **Translation Guidelines**
- Use consistent terminology
- Test with native Persian speakers
- Maintain cultural context
- Update documentation in both languages

## 🧪 Testing Guidelines

### **Backend Testing**
```bash
# Run Python tests
python -m pytest tests/

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ask -X POST -H "Content-Type: application/json" -d '{"query": "دمای فعلی چقدر است؟"}'
```

### **Frontend Testing**
```bash
# Run React tests
cd frontend && npm test

# Test components
npm run test:coverage
```

### **Integration Testing**
- Test AI chat functionality
- Test alert creation and monitoring
- Test real-time data updates
- Test Persian language support

## 📚 Documentation

### **Code Documentation**
- Write clear docstrings
- Use type hints in Python
- Comment complex logic
- Update README files

### **API Documentation**
- Document new endpoints
- Include request/response examples
- Update OpenAPI/Swagger docs
- Provide usage examples

## 🚨 Security Guidelines

### **API Security**
- Validate all inputs
- Sanitize user queries
- Prevent SQL injection
- Use secure authentication

### **Data Protection**
- Don't commit sensitive data
- Use environment variables
- Secure database connections
- Implement proper error handling

## 🎯 Feature Development

### **AI Assistant Features**
- Maintain Persian language support
- Test with real agricultural data
- Ensure response quality
- Handle edge cases gracefully

### **Alert System Features**
- Test natural language parsing
- Verify alert triggering
- Test Act/Pass functionality
- Ensure real-time monitoring

### **Dashboard Features**
- Maintain responsive design
- Test on different screen sizes
- Ensure accessibility
- Optimize performance

## 📋 Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Persian language support maintained
- [ ] No sensitive data committed
- [ ] Backward compatibility maintained
- [ ] Performance impact considered
- [ ] Security implications reviewed

## 🐛 Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Windows 10]
- Python: [e.g., 3.8.5]
- Node.js: [e.g., 16.14.0]
- Browser: [e.g., Chrome 91]

**Additional Context**
Any other relevant information.
```

## 🚀 Feature Request Template

```markdown
**Feature Description**
A clear description of the feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives**
Other solutions you've considered.

**Additional Context**
Any other relevant information.
```

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check README files
- **Code Review**: Ask for help in PRs

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation
- GitHub contributors page

Thank you for contributing to the Smart Agriculture Dashboard! 🌱
