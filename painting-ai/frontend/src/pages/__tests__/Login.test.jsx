import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent } from '../../tests/utils'
import Login from '../Login'
import * as api from '../../utils/api'
import useAuthStore from '../../store/authStore'

// Mock the API
vi.mock('../../utils/api', () => ({
  login: vi.fn(),
}))

// Mock the auth store
vi.mock('../../store/authStore')

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('Login Page', () => {
  const mockSetAuth = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.mockReturnValue({
      setAuth: mockSetAuth,
    })
  })

  it('renders login form', () => {
    renderWithProviders(<Login />)

    expect(screen.getByText('Sign in to Painting.ai')).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('displays logo and branding', () => {
    renderWithProviders(<Login />)

    expect(screen.getByText('Sign in to Painting.ai')).toBeInTheDocument()
    expect(screen.getByText(/create a new account/i)).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    renderWithProviders(<Login />)

    const registerLink = screen.getByRole('link', { name: /create a new account/i })
    expect(registerLink).toBeInTheDocument()
    expect(registerLink).toHaveAttribute('href', '/register')
  })

  it('shows demo credentials', () => {
    renderWithProviders(<Login />)

    expect(screen.getByText(/demo credentials/i)).toBeInTheDocument()
    expect(screen.getByText('Email: demo@painting.ai')).toBeInTheDocument()
    expect(screen.getByText('Password: demo123')).toBeInTheDocument()
  })

  it('updates form fields on user input', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    expect(emailInput).toHaveValue('test@example.com')
    expect(passwordInput).toHaveValue('password123')
  })

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup()
    const mockLoginResponse = {
      user: { id: 1, name: 'Test User', email: 'test@example.com' },
      access_token: 'access_token_123',
      refresh_token: 'refresh_token_123',
    }

    api.login.mockResolvedValueOnce(mockLoginResponse)
    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(api.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })

    await waitFor(() => {
      expect(mockSetAuth).toHaveBeenCalledWith(
        mockLoginResponse.user,
        mockLoginResponse.access_token,
        mockLoginResponse.refresh_token
      )
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('displays error message on login failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Invalid credentials'

    api.login.mockRejectedValueOnce({
      response: {
        data: {
          detail: errorMessage,
        },
      },
    })

    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'wrong@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('displays generic error message when no detail provided', async () => {
    const user = userEvent.setup()

    api.login.mockRejectedValueOnce({
      response: {
        data: {},
      },
    })

    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to sign in')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()

    api.login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    })
  })

  it('disables submit button during submission', async () => {
    const user = userEvent.setup()

    api.login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(submitButton).toBeDisabled()
    })
  })

  it('requires email and password fields', () => {
    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)

    expect(emailInput).toBeRequired()
    expect(passwordInput).toBeRequired()
  })

  it('has correct input types', () => {
    renderWithProviders(<Login />)

    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/password/i)

    expect(emailInput).toHaveAttribute('type', 'email')
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('renders remember me checkbox', () => {
    renderWithProviders(<Login />)

    const rememberCheckbox = screen.getByLabelText(/remember me/i)
    expect(rememberCheckbox).toBeInTheDocument()
    expect(rememberCheckbox).toHaveAttribute('type', 'checkbox')
  })

  it('renders forgot password link', () => {
    renderWithProviders(<Login />)

    const forgotLink = screen.getByText(/forgot password/i)
    expect(forgotLink).toBeInTheDocument()
  })
})
