import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Loader2, AlertCircle, RefreshCw, Zap } from 'lucide-react'
import { getProject, getProjectRooms, generateEstimate } from '../utils/api'
import { useState } from 'react'
import WallEditor from '../components/WallEditor'
import MaterialsList from '../components/MaterialsList'
import api from '../utils/api'

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

  const assemblyMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/projects/${projectId}/assembly-expansion`, {
        paint_type: estimateParams.surface_type,
        labor_rate: estimateParams.labor_rate,
      })
      return response.data
    },
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
          <p className="text-sm text-gray-600">Total Walls</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_rooms || 0}
          </p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Total Area</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_sqft?.toLocaleString() || 0}
            <span className="text-sm text-gray-500 ml-1">sqft</span>
          </p>
        </div>

        <div className="card">
          <p className="text-sm text-gray-600">Drywall Sheets</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {project.total_gallons?.toFixed(0) || 0}
            <span className="text-sm text-gray-500 ml-1">sheets</span>
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
          Takeoff Parameters
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Drywall Price ($/sheet)
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
              Finishing Level
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
              <option value="smooth_drywall">Level 4 - Standard</option>
              <option value="textured_drywall">Level 3 - Textured</option>
              <option value="smooth_plaster">Level 5 - Premium</option>
              <option value="rough_plaster">Level 2 - Garage</option>
              <option value="wood">Level 1 - Fire Tape</option>
            </select>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleGenerateEstimate}
            className="btn btn-secondary flex items-center space-x-2"
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
                <span>Generate Quick Estimate</span>
              </>
            )}
          </button>

          <button
            onClick={() => assemblyMutation.mutate()}
            className="btn btn-primary flex items-center space-x-2"
            disabled={assemblyMutation.isPending}
          >
            {assemblyMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Expanding...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                <span>Generate Detailed Material List</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Walls List with Editor */}
      <div className="card mb-8">
        <WallEditor projectId={projectId} rooms={rooms} />
      </div>

      {/* Materials List */}
      <MaterialsList
        materials={project.materials}
        laborHours={project.labor_hours}
        totalCost={project.estimated_cost}
      />
    </div>
  )
}
