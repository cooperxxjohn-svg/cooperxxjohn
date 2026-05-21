import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { userEvent } from '../../tests/utils'
import Toast from '../Toast'

describe('Toast Component', () => {
  const mockOnClose = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('renders toast with message', () => {
    render(<Toast message="Test message" onClose={mockOnClose} />)

    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('renders success toast with correct styling', () => {
    render(<Toast message="Success!" type="success" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Success!').closest('div')
    expect(toastElement?.className).toContain('green')
  })

  it('renders error toast with correct styling', () => {
    render(<Toast message="Error!" type="error" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Error!').closest('div')
    expect(toastElement?.className).toContain('red')
  })

  it('renders warning toast with correct styling', () => {
    render(<Toast message="Warning!" type="warning" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Warning!').closest('div')
    expect(toastElement?.className).toContain('yellow')
  })

  it('renders info toast with correct styling', () => {
    render(<Toast message="Info!" type="info" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Info!').closest('div')
    expect(toastElement?.className).toContain('blue')
  })

  it('defaults to info type when no type provided', () => {
    render(<Toast message="Default message" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Default message').closest('div')
    expect(toastElement?.className).toContain('blue')
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup({ delay: null })
    render(<Toast message="Test message" onClose={mockOnClose} />)

    const closeButton = screen.getByRole('button')
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after default duration', () => {
    render(<Toast message="Auto dismiss" onClose={mockOnClose} />)

    expect(mockOnClose).not.toHaveBeenCalled()

    vi.advanceTimersByTime(5000)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('auto-dismisses after custom duration', () => {
    render(<Toast message="Custom duration" onClose={mockOnClose} duration={3000} />)

    expect(mockOnClose).not.toHaveBeenCalled()

    vi.advanceTimersByTime(3000)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('does not auto-dismiss when duration is 0', () => {
    render(<Toast message="Persistent" onClose={mockOnClose} duration={0} />)

    vi.advanceTimersByTime(10000)

    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('does not auto-dismiss when duration is negative', () => {
    render(<Toast message="Persistent" onClose={mockOnClose} duration={-1} />)

    vi.advanceTimersByTime(10000)

    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('renders success icon', () => {
    const { container } = render(<Toast message="Success" type="success" onClose={mockOnClose} />)

    // CheckCircle icon should be present
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('renders error icon', () => {
    const { container } = render(<Toast message="Error" type="error" onClose={mockOnClose} />)

    // XCircle icon should be present
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('renders warning icon', () => {
    const { container } = render(<Toast message="Warning" type="warning" onClose={mockOnClose} />)

    // AlertCircle icon should be present
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('renders info icon', () => {
    const { container } = render(<Toast message="Info" type="info" onClose={mockOnClose} />)

    // Info icon should be present
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('renders close button icon', () => {
    render(<Toast message="Test" onClose={mockOnClose} />)

    const closeButton = screen.getByRole('button')
    expect(closeButton).toBeInTheDocument()

    // X icon should be present in close button
    const icon = closeButton.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('cleans up timer on unmount', () => {
    const { unmount } = render(<Toast message="Test" onClose={mockOnClose} duration={5000} />)

    unmount()

    vi.advanceTimersByTime(5000)

    expect(mockOnClose).not.toHaveBeenCalled()
  })

  it('applies animation class', () => {
    render(<Toast message="Animated" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Animated').closest('div')
    expect(toastElement?.className).toContain('animate-slide-in')
  })

  it('renders with shadow', () => {
    render(<Toast message="Shadow test" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Shadow test').closest('div')
    expect(toastElement?.className).toContain('shadow')
  })

  it('has border styling', () => {
    render(<Toast message="Border test" onClose={mockOnClose} />)

    const toastElement = screen.getByText('Border test').closest('div')
    expect(toastElement?.className).toContain('border')
  })

  it('long message displays correctly', () => {
    const longMessage = 'This is a very long message that should still display correctly in the toast component without breaking the layout or causing any issues with the styling or functionality of the component.'

    render(<Toast message={longMessage} onClose={mockOnClose} />)

    expect(screen.getByText(longMessage)).toBeInTheDocument()
  })

  it('multiple toasts can be rendered', () => {
    const { container } = render(
      <div>
        <Toast message="First toast" type="success" onClose={vi.fn()} />
        <Toast message="Second toast" type="error" onClose={vi.fn()} />
        <Toast message="Third toast" type="warning" onClose={vi.fn()} />
      </div>
    )

    expect(screen.getByText('First toast')).toBeInTheDocument()
    expect(screen.getByText('Second toast')).toBeInTheDocument()
    expect(screen.getByText('Third toast')).toBeInTheDocument()
  })

  it('icon has correct color for success type', () => {
    const { container } = render(<Toast message="Success" type="success" onClose={mockOnClose} />)

    const icons = container.querySelectorAll('svg')
    const mainIcon = icons[0] // First icon is the status icon
    expect(mainIcon?.className).toContain('green')
  })

  it('icon has correct color for error type', () => {
    const { container } = render(<Toast message="Error" type="error" onClose={mockOnClose} />)

    const icons = container.querySelectorAll('svg')
    const mainIcon = icons[0]
    expect(mainIcon?.className).toContain('red')
  })

  it('icon has correct color for warning type', () => {
    const { container } = render(<Toast message="Warning" type="warning" onClose={mockOnClose} />)

    const icons = container.querySelectorAll('svg')
    const mainIcon = icons[0]
    expect(mainIcon?.className).toContain('yellow')
  })

  it('icon has correct color for info type', () => {
    const { container } = render(<Toast message="Info" type="info" onClose={mockOnClose} />)

    const icons = container.querySelectorAll('svg')
    const mainIcon = icons[0]
    expect(mainIcon?.className).toContain('blue')
  })
})
