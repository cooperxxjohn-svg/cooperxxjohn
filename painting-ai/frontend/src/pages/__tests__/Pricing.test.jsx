import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent } from '../../tests/utils'
import Pricing from '../Pricing'
import useAuthStore from '../../store/authStore'
import api from '../../utils/api'

// Mock the auth store
vi.mock('../../store/authStore')

// Mock the API
vi.mock('../../utils/api', () => ({
  default: {
    post: vi.fn(),
  },
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('Pricing Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders pricing page with header', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument()
    expect(screen.getByText(/choose the plan that's right for your business/i)).toBeInTheDocument()
    expect(screen.getByText(/14-day free trial on all plans/i)).toBeInTheDocument()
  })

  it('displays all three pricing plans', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('Starter')).toBeInTheDocument()
    expect(screen.getByText('Pro')).toBeInTheDocument()
    expect(screen.getByText('Enterprise')).toBeInTheDocument()
  })

  it('displays plan descriptions', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('Perfect for solo contractors')).toBeInTheDocument()
    expect(screen.getByText('For growing businesses')).toBeInTheDocument()
    expect(screen.getByText('For large organizations')).toBeInTheDocument()
  })

  it('displays plan prices', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('$99')).toBeInTheDocument()
    expect(screen.getByText('$299')).toBeInTheDocument()
    expect(screen.getByText('Custom')).toBeInTheDocument()
  })

  it('marks Pro plan as most popular', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('Most Popular')).toBeInTheDocument()
  })

  it('displays plan features', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    // Starter features
    expect(screen.getByText('50 projects per month')).toBeInTheDocument()
    expect(screen.getAllByText('AI room detection').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Excel & PDF exports').length).toBeGreaterThan(0)
    expect(screen.getByText('Email support')).toBeInTheDocument()
    expect(screen.getByText('1 user')).toBeInTheDocument()

    // Pro features
    expect(screen.getByText('Unlimited projects')).toBeInTheDocument()
    expect(screen.getByText('Public API access')).toBeInTheDocument()
    expect(screen.getByText('Up to 5 team members')).toBeInTheDocument()

    // Enterprise features
    expect(screen.getByText('Everything in Pro')).toBeInTheDocument()
    expect(screen.getByText('Unlimited team members')).toBeInTheDocument()
    expect(screen.getByText('Dedicated account manager')).toBeInTheDocument()
  })

  it('redirects to register when unauthenticated user clicks subscribe', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: false })

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[0])

    // Wait a bit for the navigation to be called
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(mockNavigate).toHaveBeenCalledWith('/register')
  })

  it('creates checkout session for authenticated user', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })
    api.post.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/session' },
    })

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[0])

    await waitFor(() => {
      expect(api.post).toHaveBeenCalled()
      expect(api.post.mock.calls[0][0]).toBe('/checkout/create-session')
      expect(api.post.mock.calls[0][1].plan).toBe('starter')
      expect(api.post.mock.calls[0][1].success_url).toContain('/success')
      expect(api.post.mock.calls[0][1].cancel_url).toContain('/pricing')
    })

    await waitFor(() => {
      expect(window.location.href).toBe('https://checkout.stripe.com/session')
    })
  })

  it('shows loading state during checkout', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })
    api.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[0])

    await waitFor(() => {
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  it('handles checkout error', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })
    const errorMessage = 'Payment setup failed'
    api.post.mockRejectedValueOnce({
      response: { data: { detail: errorMessage } },
    })

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[0])

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining(errorMessage)
      )
    })
  })

  it('opens email for enterprise plan', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })

    renderWithProviders(<Pricing />)

    const contactButton = screen.getByRole('button', { name: /contact sales/i })
    await user.click(contactButton)

    await waitFor(() => {
      expect(window.location.href).toBe(
        'mailto:sales@painting.ai?subject=Enterprise Plan Inquiry'
      )
    })
  })

  it('displays FAQ section', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument()
    expect(screen.getByText(/what's included in the free trial/i)).toBeInTheDocument()
    expect(screen.getByText(/can i change plans later/i)).toBeInTheDocument()
    expect(screen.getByText(/what payment methods do you accept/i)).toBeInTheDocument()
    expect(screen.getByText(/can i cancel anytime/i)).toBeInTheDocument()
  })

  it('displays FAQ answers', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    expect(screen.getByText(/all plans include a 14-day free trial/i)).toBeInTheDocument()
    expect(screen.getByText(/you can upgrade or downgrade your plan at any time/i)).toBeInTheDocument()
    expect(screen.getByText(/we accept all major credit cards/i)).toBeInTheDocument()
    expect(screen.getByText(/you can cancel your subscription at any time/i)).toBeInTheDocument()
  })

  it('renders plan buttons with correct text', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    const startTrialButtons = screen.getAllByRole('button', { name: /start free trial/i })
    const contactSalesButton = screen.getByRole('button', { name: /contact sales/i })

    expect(startTrialButtons).toHaveLength(2) // Starter and Pro
    expect(contactSalesButton).toBeInTheDocument()
  })

  it('applies correct styling to popular plan', () => {
    useAuthStore.mockReturnValue({ isAuthenticated: false })
    renderWithProviders(<Pricing />)

    const popularBadge = screen.getByText('Most Popular')
    expect(popularBadge).toBeInTheDocument()
  })

  it('disables button during checkout', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })
    api.post.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[0])

    await waitFor(() => {
      expect(startButtons[0]).toBeDisabled()
    })
  })

  it('creates checkout for Pro plan', async () => {
    const user = userEvent.setup()
    useAuthStore.mockReturnValue({ isAuthenticated: true })
    api.post.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/session' },
    })

    renderWithProviders(<Pricing />)

    const startButtons = screen.getAllByRole('button', { name: /start free trial/i })
    await user.click(startButtons[1]) // Pro plan

    await waitFor(() => {
      expect(api.post).toHaveBeenCalled()
      expect(api.post.mock.calls[0][0]).toBe('/checkout/create-session')
      expect(api.post.mock.calls[0][1].plan).toBe('pro')
    })
  })
})
