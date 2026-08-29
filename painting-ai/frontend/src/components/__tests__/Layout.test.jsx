import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent, mockUser } from '../../tests/utils'
import Layout from '../Layout'
import useAuthStore from '../../store/authStore'

// Mock the auth store
vi.mock('../../store/authStore')

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: '/dashboard' }),
  }
})

describe('Layout Component', () => {
  const mockClearAuth = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.mockImplementation((selector) => {
      const state = {
        user: mockUser,
        clearAuth: mockClearAuth,
      }
      return selector ? selector(state) : state
    })
  })

  it('renders header with logo and branding', () => {
    renderWithProviders(<Layout />)

    expect(screen.getByText('Painting.ai')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithProviders(<Layout />)

    const projectsLink = screen.getByRole('link', { name: /projects/i })
    const newProjectButton = screen.getByRole('link', { name: /new project/i })

    expect(projectsLink).toBeInTheDocument()
    expect(newProjectButton).toBeInTheDocument()

    expect(projectsLink).toHaveAttribute('href', '/dashboard')
    expect(newProjectButton).toHaveAttribute('href', '/dashboard/upload')
  })

  it('displays user name in user menu button', () => {
    renderWithProviders(<Layout />)

    expect(screen.getByText(mockUser.name)).toBeInTheDocument()
  })

  it('toggles user menu on click', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })

    // Menu should not be visible initially
    expect(screen.queryByText('Settings')).not.toBeInTheDocument()

    // Click to open menu
    await user.click(userMenuButton)
    expect(screen.getByText('Settings')).toBeInTheDocument()

    // Click again to close menu
    await user.click(userMenuButton)
    await waitFor(() => {
      expect(screen.queryByText('Settings')).not.toBeInTheDocument()
    })
  })

  it('displays user information in dropdown', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    expect(screen.getByText(mockUser.name)).toBeInTheDocument()
    expect(screen.getByText(mockUser.email)).toBeInTheDocument()
    expect(screen.getByText(/plan:/i)).toBeInTheDocument()
    expect(screen.getByText(mockUser.plan)).toBeInTheDocument()
  })

  it('renders menu items in dropdown', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    expect(screen.getByRole('link', { name: /^settings$/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /billing/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /api keys/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
  })

  it('navigates to settings when clicking settings link', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    const settingsLink = screen.getByRole('link', { name: /^settings$/i })
    expect(settingsLink).toHaveAttribute('href', '/dashboard/settings')
  })

  it('navigates to billing when clicking billing link', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    const billingLink = screen.getByRole('link', { name: /billing/i })
    expect(billingLink).toHaveAttribute('href', '/dashboard/settings?tab=billing')
  })

  it('navigates to API keys when clicking API keys link', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    const apiKeysLink = screen.getByRole('link', { name: /api keys/i })
    expect(apiKeysLink).toHaveAttribute('href', '/dashboard/settings?tab=api')
  })

  it('closes menu when clicking settings link', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    const settingsLink = screen.getByRole('link', { name: /^settings$/i })
    await user.click(settingsLink)

    // Menu should close after clicking a link
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /sign out/i })).not.toBeInTheDocument()
    })
  })

  it('logs out user when clicking sign out', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(mockUser.name, 'i') })
    await user.click(userMenuButton)

    const signOutButton = screen.getByRole('button', { name: /sign out/i })
    await user.click(signOutButton)

    await waitFor(() => {
      expect(mockClearAuth).toHaveBeenCalled()
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })

  it('renders footer', () => {
    renderWithProviders(<Layout />)

    expect(screen.getByText(/© 2026 Painting.ai/i)).toBeInTheDocument()
  })

  it('renders footer links', () => {
    renderWithProviders(<Layout />)

    expect(screen.getByRole('link', { name: /^help$/i })).toHaveAttribute('href', '/help')
    expect(screen.getByRole('link', { name: /terms/i })).toHaveAttribute('href', '/terms')
    expect(screen.getByRole('link', { name: /privacy/i })).toHaveAttribute('href', '/privacy')
    expect(screen.getByRole('link', { name: /contact/i })).toHaveAttribute('href', 'mailto:support@painting.ai')
  })

  it('highlights active navigation link', () => {
    renderWithProviders(<Layout />)

    const projectsLink = screen.getByRole('link', { name: /projects/i })
    expect(projectsLink.className).toContain('primary')
  })

  it('displays user as fallback when no name', () => {
    const userWithoutName = { ...mockUser, name: null }
    useAuthStore.mockImplementation((selector) => {
      const state = {
        user: userWithoutName,
        clearAuth: mockClearAuth,
      }
      return selector ? selector(state) : state
    })

    renderWithProviders(<Layout />)

    expect(screen.getByText('User')).toBeInTheDocument()
  })

  it('displays trial plan with capitalized text', async () => {
    const user = userEvent.setup()
    const trialUser = { ...mockUser, plan: 'trial' }
    useAuthStore.mockImplementation((selector) => {
      const state = {
        user: trialUser,
        clearAuth: mockClearAuth,
      }
      return selector ? selector(state) : state
    })

    renderWithProviders(<Layout />)

    const userMenuButton = screen.getByRole('button', { name: new RegExp(trialUser.name, 'i') })
    await user.click(userMenuButton)

    expect(screen.getByText('trial')).toBeInTheDocument()
  })

  it('renders main content area', () => {
    renderWithProviders(<Layout />)

    // Layout should have a main element for content
    const mainElement = document.querySelector('main')
    expect(mainElement).toBeInTheDocument()
  })

  it('renders header border', () => {
    renderWithProviders(<Layout />)

    const header = document.querySelector('header')
    expect(header).toBeInTheDocument()
  })
})
