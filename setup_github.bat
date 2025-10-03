@echo off
echo ========================================
echo Smart Agriculture Dashboard - GitHub Setup
echo ========================================
echo.

echo Checking if git is initialized...
if not exist ".git" (
    echo Initializing git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

echo.
echo Adding all files to git...
git add .

echo.
echo Making initial commit...
git commit -m "Initial commit: Smart Agriculture Dashboard with AI Assistant and Persian support"

echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo 1. Go to https://github.com and create a new repository
echo 2. Name it: smart-agriculture-dashboard
echo 3. Don't initialize with README (we already have one)
echo 4. Copy the repository URL
echo 5. Run these commands:
echo.
echo    git remote add origin YOUR_REPOSITORY_URL
echo    git branch -M main
echo    git push -u origin main
echo.
echo ========================================
echo Repository URL format:
echo https://github.com/YOUR_USERNAME/smart-agriculture-dashboard.git
echo ========================================
echo.

pause
