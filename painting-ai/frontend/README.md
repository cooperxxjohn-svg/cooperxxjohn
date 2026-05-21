# Painting.ai Frontend

React-based frontend for AI-powered painting takeoffs and estimates.

## 🏗️ Architecture

### Tech Stack
- **Framework:** React 18
- **Build Tool:** Vite 5
- **Routing:** React Router v6
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **HTTP Client:** Axios
- **Styling:** Tailwind CSS 3
- **Icons:** Lucide React
- **Charts:** Recharts
- **Testing:** Vitest + Playwright

### Project Structure

```
frontend/
├── src/
│   ├── pages/               # Page components
│   │   ├── Landing.jsx      # Marketing landing page
│   │   ├── Login.jsx        # Login page
│   │   ├── Register.jsx     # Registration page
│   │   ├── Dashboard.jsx    # Project dashboard
│   │   ├── Upload.jsx       # File upload page
│   │   ├── ProjectView.jsx  # Project details & room editor
│   │   ├── Settings.jsx     # User settings
│   │   ├── Pricing.jsx      # Pricing plans
│   │   ├── Success.jsx      # Payment success
│   │   ├── Help.jsx         # Help & FAQ
│   │   ├── Terms.jsx        # Terms of service
│   │   ├── Privacy.jsx      # Privacy policy
│   │   └── NotFound.jsx     # 404 page
│   ├── components/          # Reusable components
│   │   ├── Layout.jsx       # App layout with sidebar
│   │   ├── ProtectedRoute.jsx # Auth guard
│   │   ├── ErrorBoundary.jsx  # Error handling
│   │   ├── Toast.jsx        # Toast notification
│   │   ├── ToastContainer.jsx # Toast manager
│   │   └── RoomEditor.jsx   # Room editing interface
│   ├── store/               # State management
│   │   ├── authStore.js     # Authentication state
│   │   └── toastStore.js    # Toast notifications
│   ├── utils/               # Utilities
│   │   └── api.js           # API client
│   ├── App.jsx              # Main app component
│   └── main.jsx             # Entry point
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
└── package.json             # Dependencies & scripts
```

## 🚀 Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env if needed
```

### Environment Variables

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: Analytics, monitoring
VITE_SENTRY_DSN=your-sentry-dsn
VITE_ANALYTICS_ID=your-analytics-id
```

### Development Server

```bash
# Start dev server (with hot reload)
npm run dev

# Access at http://localhost:3000
```

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview

# Build output in dist/
```

## 🧪 Testing

### Unit Tests (Vitest)

```bash
# Run tests
npm run test

# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Coverage report in coverage/
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run E2E tests in debug mode
npm run test:e2e:debug
```

### Writing Tests

**Unit Test Example:**
```javascript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Dashboard from './Dashboard'

describe('Dashboard', () => {
  it('renders projects', () => {
    render(<Dashboard />)
    expect(screen.getByText('Projects')).toBeInTheDocument()
  })
})
```

**E2E Test Example:**
```javascript
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  await page.goto('http://localhost:3000/login')
  await page.fill('input[name="email"]', 'test@example.com')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL(/.*dashboard/)
})
```

## 📱 Pages & Routes

### Public Routes
- `/` - Landing page (redirects to /dashboard if logged in)
- `/login` - Login page
- `/register` - Registration page
- `/pricing` - Pricing plans
- `/help` - Help & FAQ
- `/terms` - Terms of service
- `/privacy` - Privacy policy
- `/success` - Payment success (after Stripe checkout)

### Protected Routes (require authentication)
- `/dashboard` - Project dashboard
- `/dashboard/upload` - Upload floor plan
- `/dashboard/projects/:id` - Project details & room editor
- `/dashboard/settings` - User settings

### Error Routes
- `*` - 404 Not Found page

## 🔒 Authentication

### Auth Flow

1. **Registration:**
   ```javascript
   import { register } from './utils/api'
   
   const data = await register({
     email: 'user@example.com',
     password: 'secure-password',
     full_name: 'John Doe',
     company_name: 'ABC Painting'
   })
   // Returns: { user, access_token, refresh_token }
   ```

2. **Login:**
   ```javascript
   import { login } from './utils/api'
   import useAuthStore from './store/authStore'
   
   const data = await login({
     email: 'user@example.com',
     password: 'password'
   })
   
   // Store auth tokens
   useAuthStore.getState().setAuth(
     data.user,
     data.access_token,
     data.refresh_token
   )
   ```

3. **Automatic Token Refresh:**
   - API client automatically refreshes expired tokens
   - Redirects to login on refresh failure

4. **Logout:**
   ```javascript
   import useAuthStore from './store/authStore'
   
   useAuthStore.getState().clearAuth()
   // Redirects to login
   ```

### Protected Routes

```javascript
import ProtectedRoute from './components/ProtectedRoute'

<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

## 🎨 Styling

### Tailwind CSS

- **Configuration:** `tailwind.config.js`
- **Custom Colors:** Primary, secondary, accent
- **Responsive:** Mobile-first breakpoints
- **Dark Mode:** (Optional) Class-based

**Common Classes:**
```javascript
// Buttons
<button className="btn btn-primary">Click Me</button>
<button className="btn btn-secondary">Cancel</button>

// Cards
<div className="card">Content</div>

// Inputs
<input className="input" />

// Responsive
<div className="hidden md:block">Desktop only</div>
<div className="md:hidden">Mobile only</div>
```

### Custom Styles

Global styles in `src/index.css`:
```css
@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }
  
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}
```

## 📊 State Management

### Zustand Stores

**Auth Store (`store/authStore.js`):**
```javascript
import useAuthStore from './store/authStore'

// Get current user
const user = useAuthStore((state) => state.user)
const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

// Login
useAuthStore.getState().setAuth(user, accessToken, refreshToken)

// Logout
useAuthStore.getState().clearAuth()
```

**Toast Store (`store/toastStore.js`):**
```javascript
import useToastStore from './store/toastStore'

// Show toast
useToastStore.getState().addToast({
  message: 'Success!',
  type: 'success'
})

// Types: success, error, warning, info
```

### TanStack Query

**Fetching Data:**
```javascript
import { useQuery } from '@tanstack/react-query'
import { getProjects } from './utils/api'

const { data, isLoading, error } = useQuery({
  queryKey: ['projects'],
  queryFn: getProjects
})
```

**Mutations:**
```javascript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createProject } from './utils/api'

const queryClient = useQueryClient()

const mutation = useMutation({
  mutationFn: createProject,
  onSuccess: () => {
    // Invalidate and refetch projects
    queryClient.invalidateQueries({ queryKey: ['projects'] })
  }
})

// Usage
mutation.mutate({ name: 'New Project' })
```

## 🔌 API Integration

### API Client (`utils/api.js`)

**Configuration:**
```javascript
import api from './utils/api'

// Base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_URL

// Automatic token attachment
// Automatic token refresh on 401
```

**API Functions:**
```javascript
// Authentication
import { login, register, getCurrentUser, logout } from './utils/api'

// Projects
import { getProjects, getProject, createProject } from './utils/api'

// File Upload
import { uploadDrawing } from './utils/api'

// Rooms
import { getProjectRooms } from './utils/api'

// Estimates
import { generateEstimate } from './utils/api'
```

### Error Handling

```javascript
try {
  const data = await createProject({ name: 'Test' })
} catch (error) {
  if (error.response?.status === 401) {
    // Unauthorized - redirect to login
  } else if (error.response?.status === 422) {
    // Validation error
    const detail = error.response.data.detail
  } else {
    // Generic error
    console.error('API error:', error)
  }
}
```

## 🎯 Key Features

### File Upload

**Drag & Drop:**
```javascript
const handleDrop = (e) => {
  e.preventDefault()
  const file = e.dataTransfer.files[0]
  // Validate file type (PDF, PNG, JPG)
  // Validate file size (max 50MB)
  // Upload file
}
```

**Validation:**
- File types: `.pdf`, `.png`, `.jpg`, `.jpeg`
- Max size: 50MB
- MIME type checking

### Room Editor

**Features:**
- View room list with dimensions
- Edit room details (name, dimensions)
- Add new rooms manually
- Delete rooms
- Expand to assembly line items
- Export to Excel/PDF

**Component:** `components/RoomEditor.jsx`

### Toast Notifications

```javascript
import useToastStore from './store/toastStore'

// Success
useToastStore.getState().addToast({
  message: 'Project created successfully!',
  type: 'success'
})

// Error
useToastStore.getState().addToast({
  message: 'Failed to upload file',
  type: 'error'
})
```

### Error Boundary

Catches React errors and displays user-friendly message:

```javascript
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

Shows:
- Error icon
- User-friendly message
- Error details (development only)
- "Try Again" button
- "Go to Dashboard" button

## 📱 Responsive Design

### Breakpoints (Tailwind)
- `sm`: 640px (mobile landscape)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)
- `2xl`: 1536px (extra large)

### Testing Responsive
```bash
# Test different screen sizes
# Mobile: 320px, 375px, 414px
# Tablet: 768px, 1024px
# Desktop: 1280px, 1920px
```

### Mobile-First Approach
```javascript
// Default: mobile styles
<div className="text-sm md:text-base lg:text-lg">
  Responsive Text
</div>

// Hide on mobile, show on desktop
<div className="hidden md:block">Desktop Only</div>

// Show on mobile, hide on desktop
<div className="md:hidden">Mobile Only</div>
```

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

**vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "env": {
    "VITE_API_URL": "https://api.painting.ai"
  }
}
```

### Netlify

```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  VITE_API_URL = "https://api.painting.ai"
```

### Docker

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🐛 Debugging

### React DevTools
- Install [React DevTools](https://react.dev/learn/react-developer-tools)
- Inspect component tree
- View props & state
- Profile performance

### Vite DevTools
- Network tab for API calls
- Console for errors
- Sources for debugging

### Common Issues

**API Connection Error:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check VITE_API_URL in .env
echo $VITE_API_URL
```

**CORS Error:**
```javascript
// Backend must allow frontend origin
// Check backend CORS middleware configuration
```

**Build Errors:**
```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

## 📦 Dependencies

### Production
- `react` - UI library
- `react-dom` - React DOM renderer
- `react-router-dom` - Routing
- `@tanstack/react-query` - Data fetching
- `zustand` - State management
- `axios` - HTTP client
- `lucide-react` - Icons
- `recharts` - Charts
- `tailwindcss` - Styling
- `clsx` - Class name utility

### Development
- `vite` - Build tool
- `vitest` - Unit testing
- `@playwright/test` - E2E testing
- `@testing-library/react` - React testing utilities
- `@vitejs/plugin-react` - React plugin for Vite

## 📚 Resources

- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [React Router Docs](https://reactrouter.com/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [Zustand Docs](https://zustand-demo.pmnd.rs/)

## 🆘 Support

For issues or questions:
- Email: cooperxxjohn@gmail.com
- Check browser console for errors
- Review network tab for API failures

---

Built with React 18 & Vite 5
