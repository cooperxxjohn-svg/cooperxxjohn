import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Folder, Clock, DollarSign, Loader2, AlertCircle } from 'lucide-react'
import { getProjects } from '../utils/api'

export default function Dashboard() {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Failed to load projects</p>
          <p className="text-sm text-gray-500 mt-2">{error.message}</p>
        </div>
      </div>
    )
  }

  if (!projects || projects.length === 0) {
    return (
      <div className="text-center py-12">
        <Folder className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No takeoffs yet</h2>
        <p className="text-gray-600 mb-6">Get started by creating your first takeoff</p>
        <Link to="/dashboard/upload" className="btn btn-primary inline-flex items-center">
          Create Takeoff
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Takeoffs</h1>
        <p className="text-gray-600 mt-2">Manage your drywall takeoff projects</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Takeoffs</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{projects.length}</p>
            </div>
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <Folder className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {projects.filter(p => p.status === 'complete').length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Clock className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                ${projects.reduce((sum, p) => sum + (p.estimated_cost || 0), 0).toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Projects List */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Takeoffs</h2>

        <div className="space-y-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to={`/dashboard/projects/${project.id}`}
              className="block p-4 border rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{project.name}</h3>
                  {project.customer && (
                    <p className="text-sm text-gray-600 mt-1">{project.customer}</p>
                  )}
                  <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                    <span>{project.total_rooms || 0} walls</span>
                    <span>{project.total_sqft?.toLocaleString() || 0} sqft</span>
                    {project.estimated_cost > 0 && (
                      <span className="font-medium text-gray-900">
                        ${project.estimated_cost.toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="ml-4">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      project.status === 'complete'
                        ? 'bg-green-100 text-green-700'
                        : project.status === 'processing'
                        ? 'bg-yellow-100 text-yellow-700'
                        : project.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {project.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
