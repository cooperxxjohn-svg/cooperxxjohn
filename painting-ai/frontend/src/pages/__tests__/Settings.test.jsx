import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent, mockUser } from '../../tests/utils'
import Settings from '../Settings'
import useAuthStore from '../../store/authStore'
import api from '../../utils/api'

// Mock the auth store
vi.mock('../../store/authStore')

// Mock the API
vi.mock('../../utils/api', () => ({
  default: {
    put: vi.fn(),
    post: vi.fn(),
  },
}))

describe('Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.mockImplementation((selector) => {
      const state = {
        user: mockUser,
      }
      return selector ? selector(state) : state
    })
  })

  it('renders settings page with tabs', () => {
    renderWithProviders(<Settings />)

    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByText('Manage your account and preferences')).toBeInTheDocument()

    // Check all tabs are present
    expect(screen.getByRole('button', { name: /profile/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /api keys/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /billing/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /team/i })).toBeInTheDocument()
  })

  it('displays profile tab by default', () => {
    renderWithProviders(<Settings />)

    expect(screen.getByText('Profile Settings')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('John Doe')).toHaveValue(mockUser.name)
    expect(screen.getByPlaceholderText('you@example.com')).toHaveValue(mockUser.email)
  })

  it('switches tabs on click', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    // Click API Keys tab
    await user.click(screen.getByRole('button', { name: /api keys/i }))
    expect(screen.getByRole('heading', { name: /api keys/i })).toBeInTheDocument()

    // Click Notifications tab
    await user.click(screen.getByRole('button', { name: /notifications/i }))
    expect(screen.getByText('Notification Preferences')).toBeInTheDocument()

    // Click Billing tab
    await user.click(screen.getByRole('button', { name: /billing/i }))
    expect(screen.getByText('Billing & Subscription')).toBeInTheDocument()

    // Click Team tab
    await user.click(screen.getByRole('button', { name: /team/i }))
    expect(screen.getByText('Team Members')).toBeInTheDocument()
  })

  it('updates profile form fields', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    const nameInput = screen.getByPlaceholderText('John Doe')
    const emailInput = screen.getByPlaceholderText('you@example.com')

    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Name')

    await user.clear(emailInput)
    await user.type(emailInput, 'updated@example.com')

    expect(nameInput).toHaveValue('Updated Name')
    expect(emailInput).toHaveValue('updated@example.com')
  })

  it('saves profile changes successfully', async () => {
    const user = userEvent.setup()
    api.put.mockResolvedValueOnce({ data: { ...mockUser, name: 'Updated Name' } })

    renderWithProviders(<Settings />)

    const nameInput = screen.getByPlaceholderText('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Name')

    const saveButton = screen.getByRole('button', { name: /save changes/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(api.put).toHaveBeenCalled()
      expect(api.put.mock.calls[0][0]).toBe('/users/me')
      expect(api.put.mock.calls[0][1]).toEqual({
        name: 'Updated Name',
        email: mockUser.email,
      })
    })

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Profile updated successfully!')
    })
  })

  it('shows loading state when saving profile', async () => {
    const user = userEvent.setup()
    api.put.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Settings />)

    const saveButton = screen.getByRole('button', { name: /save changes/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/saving/i)).toBeInTheDocument()
    })
  })

  it('displays API key in masked format', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /api keys/i }))

    const apiKeyInput = screen.getByDisplayValue(mockUser.api_key)
    expect(apiKeyInput).toHaveAttribute('type', 'password')
    expect(apiKeyInput).toHaveAttribute('readonly')
  })

  it('copies API key to clipboard', async () => {
    const user = userEvent.setup()
    const writeTextMock = vi.fn()
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock,
      },
      writable: true,
      configurable: true,
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /api keys/i }))
    await user.click(screen.getByRole('button', { name: /copy/i }))

    await waitFor(() => {
      expect(writeTextMock).toHaveBeenCalledWith(mockUser.api_key)
    })

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('API key copied to clipboard!')
    })
  })

  it('displays API usage example', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /api keys/i }))

    expect(screen.getByText('Usage Example')).toBeInTheDocument()
    expect(screen.getByText(/curl -X POST/, { selector: 'pre' })).toBeInTheDocument()
  })

  it('renders notification toggles', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /notifications/i }))

    expect(screen.getByText('Project Completed')).toBeInTheDocument()
    expect(screen.getByText('Export Ready')).toBeInTheDocument()
    expect(screen.getByText('Payment Notifications')).toBeInTheDocument()
    expect(screen.getByText('Marketing Emails')).toBeInTheDocument()
  })

  it('displays current plan information', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /billing/i }))

    expect(screen.getByText('Current Plan')).toBeInTheDocument()
    expect(screen.getByText(mockUser.plan)).toBeInTheDocument()
    expect(screen.getByText(/status:/i)).toBeInTheDocument()
    expect(screen.getByText(mockUser.subscription_status)).toBeInTheDocument()
  })

  it('opens billing portal', async () => {
    const user = userEvent.setup()
    api.post.mockResolvedValueOnce({
      data: { portal_url: 'https://billing.stripe.com/portal' },
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /billing/i }))

    const manageButton = screen.getByRole('button', { name: /manage subscription/i })
    await user.click(manageButton)

    await waitFor(() => {
      expect(api.post).toHaveBeenCalled()
      expect(api.post.mock.calls[0][0]).toBe('/checkout/portal')
      expect(api.post.mock.calls[0][1].return_url).toContain('/dashboard/settings?tab=billing')
    })

    await waitFor(() => {
      expect(window.location.href).toBe('https://billing.stripe.com/portal')
    })
  })

  it('handles billing portal error', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Failed to create portal session'
    api.post.mockRejectedValueOnce({
      response: { data: { detail: errorMessage } },
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /billing/i }))

    const manageButton = screen.getByRole('button', { name: /manage subscription/i })
    await user.click(manageButton)

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringContaining(errorMessage)
      )
    })
  })

  it('displays trial end date for trial users', async () => {
    const user = userEvent.setup()
    const trialUser = { ...mockUser, plan: 'trial' }
    useAuthStore.mockImplementation((selector) => {
      const state = { user: trialUser }
      return selector ? selector(state) : state
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /billing/i }))

    expect(screen.getByText(/trial ends:/i)).toBeInTheDocument()
  })

  it('displays billing portal features list', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /billing/i }))

    expect(screen.getByText(/update payment method/i)).toBeInTheDocument()
    expect(screen.getByText(/view invoices and payment history/i)).toBeInTheDocument()
    expect(screen.getByText(/download receipts/i)).toBeInTheDocument()
    expect(screen.getByText(/cancel subscription/i)).toBeInTheDocument()
  })

  it('shows team upgrade message for non-pro users', async () => {
    const user = userEvent.setup()
    const starterUser = { ...mockUser, plan: 'starter' }
    useAuthStore.mockImplementation((selector) => {
      const state = { user: starterUser }
      return selector ? selector(state) : state
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /team/i }))

    expect(screen.getByText(/team collaboration requires a pro or enterprise plan/i)).toBeInTheDocument()
  })

  it('disables team invite for non-pro users', async () => {
    const user = userEvent.setup()
    const starterUser = { ...mockUser, plan: 'starter' }
    useAuthStore.mockImplementation((selector) => {
      const state = { user: starterUser }
      return selector ? selector(state) : state
    })

    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /team/i }))

    const emailInput = screen.getByPlaceholderText('email@example.com')
    const inviteButton = screen.getByRole('button', { name: /invite/i })

    expect(emailInput).toBeDisabled()
    expect(inviteButton).toBeDisabled()
  })

  it('displays team member limit', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    await user.click(screen.getByRole('button', { name: /team/i }))

    expect(screen.getByText(/team member limit:/i)).toBeInTheDocument()
  })

  it('highlights active tab', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Settings />)

    const profileTab = screen.getByRole('button', { name: /profile/i })
    expect(profileTab.className).toContain('primary')

    await user.click(screen.getByRole('button', { name: /api keys/i }))

    const apiTab = screen.getByRole('button', { name: /api keys/i })
    expect(apiTab.className).toContain('primary')
  })
})
