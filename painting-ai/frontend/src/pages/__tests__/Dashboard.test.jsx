import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders, mockProjects } from '../../tests/utils'
import Dashboard from '../Dashboard'
import * as api from '../../utils/api'

// Mock the API
vi.mock('../../utils/api', () => ({
  getProjects: vi.fn(),
}))

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    api.getProjects.mockImplementation(() => new Promise(() => {}))
    renderWithProviders(<Dashboard />)

    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument()
  })

  it('displays projects when data is loaded', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Projects')).toBeInTheDocument()
    })

    expect(screen.getByText('Office Building')).toBeInTheDocument()
    expect(screen.getByText('Home Renovation')).toBeInTheDocument()
    expect(screen.getByText('Apartment Complex')).toBeInTheDocument()
  })

  it('displays correct project counts in summary cards', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
    })

    // Total projects
    expect(screen.getByText('3')).toBeInTheDocument()

    // Active projects (complete status)
    expect(screen.getByText('1')).toBeInTheDocument()

    // Total value
    expect(screen.getByText('$12,500')).toBeInTheDocument()
  })

  it('displays project details correctly', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Office Building')).toBeInTheDocument()
    })

    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('5 rooms')).toBeInTheDocument()
    expect(screen.getByText('2,500 sqft')).toBeInTheDocument()
    expect(screen.getByText('$12,500')).toBeInTheDocument()
  })

  it('displays project status badges with correct styling', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('complete')).toBeInTheDocument()
    })

    const completeStatus = screen.getByText('complete')
    const processingStatus = screen.getByText('processing')
    const failedStatus = screen.getByText('failed')

    expect(completeStatus).toBeInTheDocument()
    expect(processingStatus).toBeInTheDocument()
    expect(failedStatus).toBeInTheDocument()

    // Check that they have different styling
    expect(completeStatus.className).toContain('green')
    expect(processingStatus.className).toContain('yellow')
    expect(failedStatus.className).toContain('red')
  })

  it('shows empty state when no projects exist', async () => {
    api.getProjects.mockResolvedValueOnce([])
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('No projects yet')).toBeInTheDocument()
    })

    expect(screen.getByText(/get started by creating your first project/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /create project/i })).toBeInTheDocument()
  })

  it('shows empty state when projects is null', async () => {
    api.getProjects.mockResolvedValueOnce(null)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('No projects yet')).toBeInTheDocument()
    })
  })

  it('displays error state when API call fails', async () => {
    api.getProjects.mockRejectedValueOnce(new Error('Network error'))
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load projects')).toBeInTheDocument()
    })

    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('renders create project link in empty state', async () => {
    api.getProjects.mockResolvedValueOnce([])
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('No projects yet')).toBeInTheDocument()
    })

    const createLink = screen.getByRole('link', { name: /create project/i })
    expect(createLink).toHaveAttribute('href', '/new')
  })

  it('renders project links with correct href', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Office Building')).toBeInTheDocument()
    })

    const projectLinks = screen.getAllByRole('link')
    const projectLink = projectLinks.find(link =>
      link.getAttribute('href') === '/projects/1'
    )

    expect(projectLink).toBeInTheDocument()
  })

  it('displays customer name when available', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    })

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('Property Management LLC')).toBeInTheDocument()
  })

  it('handles projects without estimated cost', async () => {
    const projectsWithoutCost = [
      {
        id: 1,
        name: 'Test Project',
        status: 'processing',
        total_rooms: 2,
        total_sqft: 1000,
        estimated_cost: 0,
      },
    ]

    api.getProjects.mockResolvedValueOnce(projectsWithoutCost)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument()
    })

    // Should not display $0 in the project card
    expect(screen.getByText('2 rooms')).toBeInTheDocument()
    expect(screen.getByText('1,000 sqft')).toBeInTheDocument()
  })

  it('displays zero values in summary when no complete projects', async () => {
    const processingProjects = [
      {
        id: 1,
        name: 'Processing Project',
        status: 'processing',
        total_rooms: 0,
        total_sqft: 0,
        estimated_cost: 0,
      },
    ]

    api.getProjects.mockResolvedValueOnce(processingProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
    })

    // Should show 1 total project but 0 active and $0 value
    expect(screen.getByText('$0')).toBeInTheDocument()
  })

  it('renders summary card icons', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
    })

    // Check that summary cards exist
    expect(screen.getByText('Active Projects')).toBeInTheDocument()
    expect(screen.getByText('Total Value')).toBeInTheDocument()
  })

  it('displays page header and description', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Projects')).toBeInTheDocument()
    })

    expect(screen.getByText('Manage your painting takeoff projects')).toBeInTheDocument()
  })

  it('displays recent projects section', async () => {
    api.getProjects.mockResolvedValueOnce(mockProjects)
    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Recent Projects')).toBeInTheDocument()
    })
  })
})
