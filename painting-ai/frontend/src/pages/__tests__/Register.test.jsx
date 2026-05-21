import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, userEvent } from '../../tests/utils'
import Register from '../Register'
import * as api from '../../utils/api'
import useAuthStore from '../../store/authStore'

// Mock the API
vi.mock('../../utils/api', () => ({
  register: vi.fn(),
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

describe('Register Page', () => {
  const mockSetAuth = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    useAuthStore.mockReturnValue({
      setAuth: mockSetAuth,
    })
  })

  it('renders registration form', () => {
    renderWithProviders(<Register />)

    expect(screen.getByText('Create your account')).toBeInTheDocument()
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
  })

  it('displays logo and branding', () => {
    renderWithProviders(<Register />)

    expect(screen.getByText('Create your account')).toBeInTheDocument()
    expect(screen.getByText(/sign in to your account/i)).toBeInTheDocument()
  })

  it('renders link to login page', () => {
    renderWithProviders(<Register />)

    const loginLink = screen.getByRole('link', { name: /sign in to your account/i })
    expect(loginLink).toBeInTheDocument()
    expect(loginLink).toHaveAttribute('href', '/login')
  })

  it('shows free trial information', () => {
    renderWithProviders(<Register />)

    expect(screen.getByText(/14-day free trial included/i)).toBeInTheDocument()
    expect(screen.getByText(/no credit card required/i)).toBeInTheDocument()
  })

  it('updates form fields on user input', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Register />)

    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const companyInput = screen.getByLabelText(/company name/i)

    await user.type(nameInput, 'John Doe')
    await user.type(emailInput, 'john@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(companyInput, 'Acme Corp')

    expect(nameInput).toHaveValue('John Doe')
    expect(emailInput).toHaveValue('john@example.com')
    expect(passwordInput).toHaveValue('password123')
    expect(companyInput).toHaveValue('Acme Corp')
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const mockRegisterResponse = {
      user: { id: 1, name: 'John Doe', email: 'john@example.com' },
      tokens: {
        access_token: 'access_token_123',
        refresh_token: 'refresh_token_123',
      },
    }

    api.register.mockResolvedValueOnce(mockRegisterResponse)
    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')
    await user.type(screen.getByLabelText(/company name/i), 'Acme Corp')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(api.register).toHaveBeenCalled()
      const callArgs = api.register.mock.calls[0][0]
      expect(callArgs).toEqual({
        name: 'John Doe',
        email: 'john@example.com',
        password: 'password123',
        organization_name: 'Acme Corp',
      })
    })

    await waitFor(() => {
      expect(mockSetAuth).toHaveBeenCalledWith(
        mockRegisterResponse.user,
        mockRegisterResponse.tokens.access_token,
        mockRegisterResponse.tokens.refresh_token
      )
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('submits form without optional company name', async () => {
    const user = userEvent.setup()
    const mockRegisterResponse = {
      user: { id: 1, name: 'John Doe', email: 'john@example.com' },
      tokens: {
        access_token: 'access_token_123',
        refresh_token: 'refresh_token_123',
      },
    }

    api.register.mockResolvedValueOnce(mockRegisterResponse)
    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(api.register).toHaveBeenCalled()
      const callArgs = api.register.mock.calls[0][0]
      expect(callArgs).toEqual({
        name: 'John Doe',
        email: 'john@example.com',
        password: 'password123',
        organization_name: '',
      })
    })
  })

  it('displays error message on registration failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Email already exists'

    api.register.mockRejectedValueOnce({
      response: {
        data: {
          detail: errorMessage,
        },
      },
    })

    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'existing@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('displays generic error message when no detail provided', async () => {
    const user = userEvent.setup()

    api.register.mockRejectedValueOnce({
      response: {
        data: {},
      },
    })

    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Failed to create account')).toBeInTheDocument()
    })
  })

  it('shows loading state during submission', async () => {
    const user = userEvent.setup()

    api.register.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/creating account/i)).toBeInTheDocument()
    })
  })

  it('disables submit button during submission', async () => {
    const user = userEvent.setup()

    api.register.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderWithProviders(<Register />)

    await user.type(screen.getByLabelText(/full name/i), 'John Doe')
    await user.type(screen.getByLabelText(/email address/i), 'john@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')

    const submitButton = screen.getByRole('button', { name: /create account/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(submitButton).toBeDisabled()
    })
  })

  it('requires name, email, and password fields', () => {
    renderWithProviders(<Register />)

    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const companyInput = screen.getByLabelText(/company name/i)

    expect(nameInput).toBeRequired()
    expect(emailInput).toBeRequired()
    expect(passwordInput).toBeRequired()
    expect(companyInput).not.toBeRequired()
  })

  it('enforces minimum password length', () => {
    renderWithProviders(<Register />)

    const passwordInput = screen.getByLabelText(/^password/i)
    expect(passwordInput).toHaveAttribute('minLength', '8')
  })

  it('displays password requirement hint', () => {
    renderWithProviders(<Register />)

    expect(screen.getByText(/must be at least 8 characters/i)).toBeInTheDocument()
  })

  it('has correct input types', () => {
    renderWithProviders(<Register />)

    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const companyInput = screen.getByLabelText(/company name/i)

    expect(nameInput).toHaveAttribute('type', 'text')
    expect(emailInput).toHaveAttribute('type', 'email')
    expect(passwordInput).toHaveAttribute('type', 'password')
    expect(companyInput).toHaveAttribute('type', 'text')
  })

  it('has appropriate placeholder text', () => {
    renderWithProviders(<Register />)

    expect(screen.getByPlaceholderText('John Doe')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Acme Painting Co.')).toBeInTheDocument()
  })
})
