import { render } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a custom render function that includes providers
export function renderWithProviders(ui, options = {}) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  const Wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )

  return render(ui, { wrapper: Wrapper, ...options })
}

// Mock user data
export const mockUser = {
  id: 1,
  name: 'Test User',
  email: 'test@example.com',
  plan: 'pro',
  subscription_status: 'active',
  api_key: 'test_api_key_123',
  settings: {
    trial_ends: '2026-06-01',
  },
}

// Mock project data
export const mockProjects = [
  {
    id: 1,
    name: 'Office Building',
    customer: 'Acme Corp',
    status: 'complete',
    total_rooms: 5,
    total_sqft: 2500,
    estimated_cost: 12500,
    created_at: '2026-05-01',
  },
  {
    id: 2,
    name: 'Home Renovation',
    customer: 'John Doe',
    status: 'processing',
    total_rooms: 3,
    total_sqft: 1200,
    estimated_cost: 0,
    created_at: '2026-05-10',
  },
  {
    id: 3,
    name: 'Apartment Complex',
    customer: 'Property Management LLC',
    status: 'failed',
    total_rooms: 0,
    total_sqft: 0,
    estimated_cost: 0,
    created_at: '2026-05-15',
  },
]

// Export everything
export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'
