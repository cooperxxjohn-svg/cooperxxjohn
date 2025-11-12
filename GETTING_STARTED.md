# TakeoffAI - Getting Started Guide

Welcome to TakeoffAI! This guide will help you get your professional BOQ estimation platform up and running in minutes.

## 🎉 What You Got

A complete, production-ready web application with:

### 🎨 Professional React Frontend
- **Landing Page**: Investor-ready with hero, features, pricing
- **Estimation Interface**: Drag-and-drop file upload, real-time processing
- **Results Dashboard**: Interactive BOQ table, validation, downloads
- **Dark/Light Theme**: Automatic detection + manual toggle
- **Mobile Responsive**: Perfect on all devices

### ⚡ Powerful Flask Backend
- **AI-Powered**: Claude Vision for drawing analysis
- **CPWD Compliant**: Automatic validation
- **Multiple Exports**: Excel, PDF, CSV, JSON
- **Production Ready**: Gunicorn, Docker, monitoring

## 🚀 Quick Start (5 Minutes)

### 1. Start the Backend

```bash
cd /home/user/cooperxxjohn

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the backend
./run_web.sh
```

Backend will start at: **http://localhost:5000**

### 2. Start the Frontend

Open a new terminal:

```bash
cd /home/user/cooperxxjohn/frontend

# Install dependencies (first time only)
npm install

# Set up environment
cp .env.local.example .env.local
# Default API URL is http://localhost:5000 (no need to change)

# Run the frontend
npm run dev
```

Frontend will start at: **http://localhost:3000**

### 3. Try It Out!

1. Open **http://localhost:3000** in your browser
2. Click "Try Demo" or "Get Started"
3. Upload a construction drawing PDF
4. Fill in project details
5. Click "Generate BOQ Estimate"
6. Wait 2-3 minutes for AI processing
7. View and download your BOQ!

## 📁 Project Structure

```
cooperxxjohn/
├── frontend/                    # React/Next.js app
│   ├── src/
│   │   ├── components/          # UI components
│   │   │   ├── landing/         # Hero, Features, Pricing
│   │   │   ├── estimate/        # Upload, Form, Processing
│   │   │   └── results/         # BOQ Table, Summary
│   │   ├── lib/                 # API client, theme, utils
│   │   ├── pages/               # Landing, Estimate, Results
│   │   └── styles/              # Global CSS
│   ├── package.json
│   └── README.md
│
├── [Backend Files]              # Flask app, BOQ engine
│   ├── web_app.py               # Flask server
│   ├── boq_estimator.py         # Core engine
│   ├── templates/               # HTML templates
│   └── WEB_APP_README.md
│
└── TAKEOFFAI_README.md          # Complete overview
```

## 🎯 Key Features

### Landing Page
- Professional hero section
- 9 feature highlights
- How it works (4 steps)
- Pricing plans (3 tiers)

### Upload Interface
- Drag-and-drop file upload
- Multiple file support
- Project details form
- Real-time validation

### Results Display
- Total cost calculation
- CPWD validation status
- Category breakdown
- Interactive BOQ table
- Material/labour details
- Download in 4 formats

## 🛠️ Customization

### Change Branding

1. **App Name**: Edit `frontend/.env.local`
   ```
   NEXT_PUBLIC_APP_NAME=YourCompanyName
   ```

2. **Colors**: Edit `frontend/tailwind.config.js`
   ```javascript
   colors: {
     primary: { 600: '#your-color' }
   }
   ```

3. **Logo**: Replace icon in `frontend/src/components/Header.tsx`

### Change Content

- **Landing page text**: Edit `frontend/src/components/landing/*.tsx`
- **Features**: Modify `Features.tsx`
- **Pricing**: Update `Pricing.tsx`

## 🚢 Deployment

### Frontend (Vercel - Easiest)

1. Push code to GitHub
2. Go to https://vercel.com
3. Click "New Project"
4. Import your repo
5. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your backend URL
6. Deploy!

### Backend (Docker - Recommended)

```bash
cd /home/user/cooperxxjohn
docker-compose -f docker-compose.web.yml up -d
```

See deployment guides:
- `frontend/README.md` - Frontend deployment
- `WEB_APP_README.md` - Backend deployment

## 📚 Documentation

- **This File**: Quick start guide
- **TAKEOFFAI_README.md**: Complete platform overview
- **frontend/README.md**: Frontend documentation
- **WEB_APP_README.md**: Backend documentation
- **QUICKSTART_WEB.md**: Backend quick start

## 🎨 Screenshots

### Landing Page
Beautiful hero section with gradient backgrounds, animated cards, and compelling CTAs.

### Estimation Interface
Clean file upload with drag-and-drop, project details form, and real-time processing feedback.

### Results Dashboard
Professional BOQ display with:
- Project summary card
- Total cost with GST
- CPWD validation status
- Category-wise breakdown
- Interactive table with expandable rows
- Material and labour breakdown
- Download buttons (Excel, PDF, CSV, JSON)

## 🔧 Development

### Frontend Development
```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm run lint         # Check code quality
```

### Backend Development
```bash
python web_app.py    # Development server
gunicorn --config gunicorn_config.py web_app:app  # Production
```

## ❓ Troubleshooting

### Port Already in Use

**Frontend**:
```bash
# Use different port
PORT=3001 npm run dev
```

**Backend**:
```bash
PORT=5001 ./run_web.sh
# Update frontend .env.local with new URL
```

### API Connection Error

1. Check backend is running: `http://localhost:5000/health`
2. Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local`
3. Check CORS settings in Flask

### Build Errors

```bash
# Clean install
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

## 🎓 Next Steps

1. **Customize Branding**: Change colors, logo, app name
2. **Add Content**: Update landing page text and images
3. **Test Thoroughly**: Upload various drawing types
4. **Deploy to Production**: Use Vercel + Docker
5. **Monitor Performance**: Set up analytics
6. **Gather Feedback**: Test with real contractors

## 📞 Support

- **Issues**: Check GitHub issues
- **Documentation**: See README files
- **Email**: support@takeoffai.com

## 🌟 What's Included

✅ Professional landing page with animations
✅ File upload with drag-and-drop
✅ Real-time processing feedback
✅ Interactive BOQ results display
✅ CPWD validation display
✅ Multiple download formats
✅ Dark/light theme toggle
✅ Mobile responsive design
✅ API client with error handling
✅ TypeScript for type safety
✅ Production-ready configuration
✅ Docker deployment files
✅ Complete documentation

## 🎉 You're Ready!

Your TakeoffAI platform is ready to use! Follow the Quick Start above to get running in 5 minutes.

**Pro Tips**:
- Start backend first, then frontend
- Use Chrome/Firefox for best experience
- Check console for any errors
- Read the detailed READMEs for advanced features

---

**Built with ❤️ for Indian government contractors**

Powered by Claude AI | CPWD Compliant | Production Ready
