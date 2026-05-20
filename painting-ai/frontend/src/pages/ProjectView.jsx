import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { getProject, getProjectRooms, generateEstimate } from '../utils/api'
import { useState } from 'react'

export default function ProjectView() {
  const { projectId } = useParams()
  const queryClient = useQueryClient()
  const [estimateParams, setEstimateParams] = useState({
    paint_price: 55.0,
    labor_rate: 50.0,
    surface_type: 'smooth_drywall',
  })

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
  })

  const { data: roomsData, isLoading: roomsLoading } = useQuery({
    queryKey: ['rooms', projectId],
    queryFn: () => getProjectRooms(projectId),
    enabled: !!project,
  })

  const estimateMutation = useMutation({
    mutationFn: () => generateEstimate(projectId, estimateParams),
    onSuccess: () => {
      queryClient.invalidateQueries(['project', projectId])
    },
  })

  const handleGenerateEstimate = () => {
    estimateMutation.mutate()
  }

  const handleExportExcel = () => {
    window.open(`/api/projects/${projectId}/export/excel`, '_blank')
  }

  const handleExportPDF = () => {
    window.open(`/api/projects/${projectId}/export/pdf`, '_blank')
  }

  if (projectLoading || roomsLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Project not found</p>
        </div>
      </div>
    )
  }

  const rooms = roomsData?.rooms || []

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        {project.customer && (
          <p className="text-gray-600 mt-2">Customer: {project.customer}</p>
        )}

        <div className="flex items-center space-x-3 mt-4">
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              project.status === 'complete'
                ? 'bg-green-100 text-green-700'
                : project.status === 'processing'
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {project.status}
          </span>

          <div className="flex space-x-2">
            <button
              onClick={handleExportExcel}
              className="btn btn-secondary flex items-center space-x-2"
              disabled={project.status !== 'complete'}
            >
              <Download className="w-4 h-4" />
              <span>Export Excel</span>
            </button>

            <button
              onClick={handleExportPDF}
              className="btn btn-secondary flex items-center space-x-2"
              disabled={project.status !== 'complete'}
            >
              <Download className="w-4 h-4" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-sm text-gray-600">Total Rooms</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_rooms || 0}
          </p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Paintable Area</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_sqft?.toLocaleString() || 0}
            <span className="text-sm text-gray-500 ml-1">sqft</span>
          </p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Paint Needed</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_gallons?.toFixed(0) || 0}
            <span className="text-sm text-gray-500 ml-1">gal</span>
          </p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Estimated Cost</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            ${project.estimated_cost?.toLocaleString() || 0}
          </p>
        </div>
      </div>

      {/* Estimate Parameters */}
      <div className="card mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Estimate Parameters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Paint Price ($/gallon)
            </label>
            <input
              type="number"
              className="input"
              value={estimateParams.paint_price}
              onChange={(e) =>
                setEstimateParams({
                  ...estimateParams,
                  paint_price: parseFloat(e.target.value),
                })
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Labor Rate ($/hour)
            </label>
            <input
              type="number"
              className="input"
              value={estimateParams.labor_rate}
              onChange={(e) =>
                setEstimateParams({
                  ...estimateParams,
                  labor_rate: parseFloat(e.target.value),
                })
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Surface Type
            </label>
            <select
              className="input"
              value={estimateParams.surface_type}
              onChange={(e) =>
                setEstimateParams({
                  ...estimateParams,
                  surface_type: e.target.value,
                })
              }
            >
              <option value="smooth_drywall">Smooth Drywall</option>
              <option value="textured_drywall">Textured Drywall</option>
              <option value="smooth_plaster">Smooth Plaster</option>
              <option value="rough_plaster">Rough Plaster</option>
              <option value="wood">Wood</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerateEstimate}
          className="btn btn-primary flex items-center space-x-2"
          disabled={estimateMutation.isPending}
        >
          {estimateMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              <span>Generate Estimate</span>
            </>
          )}
        </button>
      </div>

      {/* Rooms List */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Rooms ({rooms.length})
        </h2>

        {rooms.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {project.status === 'processing' ? (
              <div>
                <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-2" />
                <p>Processing drawing...</p>
              </div>
            ) : (
              <p>No rooms detected yet</p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {rooms.map((room) => (
              <div key={room.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{room.name}</h3>
                    {room.dimensions && (
                      <p className="text-sm text-gray-600 mt-1">
                        {room.dimensions.length}' × {room.dimensions.width}' × {room.dimensions.height}'
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Total Area</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {room.total_area?.toFixed(0)} sqft
                    </p>
                  </div>
                </div>

                {/* Surfaces */}
                {room.surfaces && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 pt-3 border-t">
                    {Object.entries(room.surfaces).map(([name, surface]) => (
                      <div key={name} className="text-center">
                        <p className="text-xs text-gray-600 uppercase">{name}</p>
                        <p className="text-sm font-medium text-gray-900 mt-1">
                          {surface.area?.toFixed(0)} sqft
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
