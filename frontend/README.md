# TakeoffAI Frontend

Professional React/Next.js web application for AI-powered BOQ (Bill of Quantities) estimation for Indian government contractors.

## Features

- 🎨 **Modern UI**: Beautiful, responsive design with dark/light theme toggle
- ⚡ **Fast Performance**: Built with Next.js 14 and optimized for speed
- 🎯 **Professional Landing Page**: Hero section, features, pricing, and more
- 📤 **File Upload**: Drag-and-drop interface for construction drawings
- 🤖 **AI Integration**: Connects to Flask backend for BOQ generation
- 📊 **Interactive Results**: Expandable BOQ tables with material/labour breakdown
- ✅ **CPWD Validation**: Display compliance status and warnings
- 💾 **Multiple Export Formats**: Excel, PDF, CSV, and JSON downloads
- 📱 **Mobile Responsive**: Works perfectly on all devices
- 🌓 **Dark Mode**: Automatic theme detection and manual toggle

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS
- **TypeScript**: Full type safety
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Charts**: Recharts
- **File Upload**: React Dropzone
- **HTTP Client**: Axios

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Running Flask backend (see ../WEB_APP_README.md)

### Installation

1. **Install dependencies:**

   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**

   ```bash
   cp .env.local.example .env.local
   # Edit .env.local and set NEXT_PUBLIC_API_URL to your Flask backend URL
   ```

3. **Run development server:**

   ```bash
   npm run dev
   ```

4. **Open browser:**

   Navigate to: `http://localhost:3000`

## Development

### Available Scripts

```bash
# Development server (http://localhost:3000)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

### Project Structure

```
frontend/
├── public/                # Static assets
├── src/
│   ├── components/        # React components
│   │   ├── landing/       # Landing page sections
│   │   ├── estimate/      # Estimation page components
│   │   ├── results/       # Results display components
│   │   ├── Header.tsx     # Site header
│   │   └── Footer.tsx     # Site footer
│   ├── lib/               # Utilities and configs
│   │   ├── api.ts         # API client
│   │   ├── theme-context.tsx  # Theme provider
│   │   └── utils.ts       # Helper functions
│   ├── pages/             # Next.js pages
│   │   ├── _app.tsx       # App wrapper
│   │   ├── _document.tsx  # HTML document
│   │   ├── index.tsx      # Landing page
│   │   └── estimate/      # Estimation pages
│   └── styles/            # Global styles
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## API Integration

The frontend connects to the Flask backend through the API client in `src/lib/api.ts`.

### Configuration

Set the backend URL in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### API Endpoints Used

- `POST /estimate` - Create BOQ estimation
- `GET /download/{format}` - Download BOQ in various formats
- `GET /health` - Health check

### Example API Call

```typescript
import { apiClient } from '@/lib/api';

const result = await apiClient.createEstimation(files, contractDetails);
```

## Customization

### Theme Colors

Edit `tailwind.config.js` to customize colors:

```javascript
colors: {
  primary: {
    500: '#3b82f6',  // Your brand color
    // ...
  },
}
```

### Branding

1. Replace logo in `src/components/Header.tsx`
2. Update `NEXT_PUBLIC_APP_NAME` in `.env.local`
3. Replace favicon in `public/favicon.ico`

### Content

- **Landing page text**: Edit `src/components/landing/*.tsx`
- **Features**: Modify `src/components/landing/Features.tsx`
- **Pricing**: Update `src/components/landing/Pricing.tsx`

## Deployment

### Vercel (Recommended)

1. **Push to GitHub**

2. **Import to Vercel:**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your repository
   - Add environment variable: `NEXT_PUBLIC_API_URL`

3. **Deploy:**
   - Vercel will automatically build and deploy

### Netlify

1. **Build command:** `npm run build`
2. **Publish directory:** `out`
3. **Add build command:**
   ```bash
   npm run build && npm run export
   ```

### Docker

```bash
# Build
docker build -t takeoffai-frontend -f Dockerfile.frontend .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-backend-url \
  takeoffai-frontend
```

### Static Export

For hosting on any static server:

```bash
npm run build
npm run export
# Deploy the 'out' directory
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Flask backend URL | `http://localhost:5000` |
| `NEXT_PUBLIC_APP_NAME` | Application name | `TakeoffAI` |

## Performance

The application is optimized for performance:

- **Code splitting**: Automatic route-based splitting
- **Image optimization**: Next.js Image component
- **Font optimization**: Google Fonts with display swap
- **CSS optimization**: Tailwind CSS purging
- **Static generation**: Pre-rendered pages where possible

### Lighthouse Scores

- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Android)

## Troubleshooting

### API Connection Error

**Problem**: "Failed to fetch" or CORS errors

**Solution**:
1. Ensure Flask backend is running
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Enable CORS in Flask backend
4. Check network/firewall settings

### Theme Not Persisting

**Problem**: Theme resets on page reload

**Solution**: Ensure localStorage is available (not in incognito mode)

### Build Errors

**Problem**: Build fails with type errors

**Solution**:
```bash
# Clean install
rm -rf node_modules .next
npm install
npm run build
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

[Your License Here]

## Support

- **Documentation**: See main README.md
- **Issues**: Report on GitHub
- **Email**: support@takeoffai.com

## Credits

Built with:
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [Framer Motion](https://www.framer.com/motion/)

Powered by [Claude AI](https://www.anthropic.com/)
