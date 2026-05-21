import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Edit2, Trash2, Plus, Save, X, Loader2 } from 'lucide-react'
import api from '../utils/api'

export default function WallEditor({ projectId, rooms = [] }) {
  const queryClient = useQueryClient()
  const [editingWall, setEditingWall] = useState(null)
  const [addingWall, setAddingWall] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    dimensions: { length: 0, width: 0, height: 0 },
    notes: '',
    wall_type: 'interior',
    openings: 0,
  })

  const updateWallMutation = useMutation({
    mutationFn: async ({ wallId, updates }) => {
      const response = await api.put(`/projects/${projectId}/rooms/${wallId}`, updates)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
      setEditingWall(null)
    },
  })

  const deleteWallMutation = useMutation({
    mutationFn: async (wallId) => {
      const response = await api.delete(`/projects/${projectId}/rooms/${wallId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
    },
  })

  const addWallMutation = useMutation({
    mutationFn: async (wallData) => {
      const response = await api.post(`/projects/${projectId}/rooms`, wallData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
      setAddingWall(false)
      setFormData({
        name: '',
        dimensions: { length: 0, width: 0, height: 0 },
        notes: '',
        wall_type: 'interior',
        openings: 0,
      })
    },
  })

  const handleEdit = (wall) => {
    setEditingWall(wall.id)
    setFormData({
      name: wall.name,
      dimensions: wall.dimensions || { length: 0, width: 0, height: 0 },
      notes: wall.notes || '',
      wall_type: wall.wall_type || 'interior',
      openings: wall.openings || 0,
    })
  }

  const handleSave = (wallId) => {
    updateWallMutation.mutate({ wallId, updates: formData })
  }

  const handleDelete = (wallId) => {
    if (confirm('Are you sure you want to delete this wall?')) {
      deleteWallMutation.mutate(wallId)
    }
  }

  const handleAddWall = () => {
    addWallMutation.mutate(formData)
  }

  const handleCancel = () => {
    setEditingWall(null)
    setAddingWall(false)
    setFormData({
      name: '',
      dimensions: { length: 0, width: 0, height: 0 },
      notes: '',
      wall_type: 'interior',
      openings: 0,
    })
  }

  const calculateLinearFootage = (dimensions) => {
    if (!dimensions) return 0
    return dimensions.length || 0
  }

  const calculateArea = (dimensions) => {
    if (!dimensions) return 0
    const { length, height } = dimensions
    return length * height
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Walls Detected ({rooms.length})
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Review AI detections and make corrections
          </p>
        </div>
        <button
          onClick={() => setAddingWall(true)}
          className="btn btn-secondary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Wall</span>
        </button>
      </div>

      {/* Add Wall Form */}
      {addingWall && (
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-gray-900 mb-4">Add New Wall</h3>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Wall Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input"
                  placeholder="North Wall"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Wall Type
                </label>
                <select
                  value={formData.wall_type}
                  onChange={(e) => setFormData({ ...formData, wall_type: e.target.value })}
                  className="input"
                >
                  <option value="interior">Interior</option>
                  <option value="exterior">Exterior</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Linear Footage (ft)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.dimensions.length}
                  onChange={(e) => setFormData({
                    ...formData,
                    dimensions: { ...formData.dimensions, length: parseFloat(e.target.value) || 0 }
                  })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Height (ft)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.dimensions.height}
                  onChange={(e) => setFormData({
                    ...formData,
                    dimensions: { ...formData.dimensions, height: parseFloat(e.target.value) || 0 }
                  })}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Openings (doors/windows)
                </label>
                <input
                  type="number"
                  value={formData.openings}
                  onChange={(e) => setFormData({ ...formData, openings: parseInt(e.target.value) || 0 })}
                  className="input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (optional)
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="input"
                rows="2"
                placeholder="Additional details..."
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={handleCancel}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <X className="w-4 h-4" />
                <span>Cancel</span>
              </button>
              <button
                onClick={handleAddWall}
                disabled={addWallMutation.isPending || !formData.name}
                className="btn btn-primary flex items-center space-x-2"
              >
                {addWallMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Adding...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Add Wall</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Walls List */}
      {rooms.length === 0 && !addingWall ? (
        <div className="text-center py-8 text-gray-500">
          <p>No walls detected yet</p>
          <p className="text-sm mt-1">Upload a floor plan to get started</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rooms.map((wall) => (
            <div key={wall.id} className="border rounded-lg p-4">
              {editingWall === wall.id ? (
                // Edit Mode
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Wall Name
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Wall Type
                      </label>
                      <select
                        value={formData.wall_type}
                        onChange={(e) => setFormData({ ...formData, wall_type: e.target.value })}
                        className="input"
                      >
                        <option value="interior">Interior</option>
                        <option value="exterior">Exterior</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Linear Footage (ft)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={formData.dimensions.length}
                        onChange={(e) => setFormData({
                          ...formData,
                          dimensions: { ...formData.dimensions, length: parseFloat(e.target.value) || 0 }
                        })}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Height (ft)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={formData.dimensions.height}
                        onChange={(e) => setFormData({
                          ...formData,
                          dimensions: { ...formData.dimensions, height: parseFloat(e.target.value) || 0 }
                        })}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Openings
                      </label>
                      <input
                        type="number"
                        value={formData.openings}
                        onChange={(e) => setFormData({ ...formData, openings: parseInt(e.target.value) || 0 })}
                        className="input"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={handleCancel}
                      className="btn btn-secondary flex items-center space-x-2"
                    >
                      <X className="w-4 h-4" />
                      <span>Cancel</span>
                    </button>
                    <button
                      onClick={() => handleSave(wall.id)}
                      disabled={updateWallMutation.isPending}
                      className="btn btn-primary flex items-center space-x-2"
                    >
                      {updateWallMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          <span>Save</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                // View Mode
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-gray-900">{wall.name}</h3>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        wall.wall_type === 'exterior'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {wall.wall_type || 'interior'}
                      </span>
                    </div>
                    {wall.dimensions && (
                      <div className="mt-2 space-y-1">
                        <p className="text-sm text-gray-600">
                          Linear Footage: <span className="font-medium text-gray-900">
                            {calculateLinearFootage(wall.dimensions).toFixed(1)} ft
                          </span>
                        </p>
                        <p className="text-sm text-gray-600">
                          Height: <span className="font-medium text-gray-900">
                            {wall.dimensions.height}'
                          </span>
                        </p>
                        <p className="text-sm text-gray-600">
                          Area: <span className="font-medium text-gray-900">
                            {calculateArea(wall.dimensions).toFixed(0)} sqft
                          </span>
                        </p>
                        {(wall.openings || 0) > 0 && (
                          <p className="text-sm text-gray-600">
                            Openings: <span className="font-medium text-gray-900">
                              {wall.openings}
                            </span>
                          </p>
                        )}
                      </div>
                    )}
                    {wall.notes && (
                      <p className="text-sm text-gray-600 mt-2">{wall.notes}</p>
                    )}
                  </div>

                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(wall)}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded"
                      title="Edit wall"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(wall.id)}
                      disabled={deleteWallMutation.isPending}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Delete wall"
                    >
                      {deleteWallMutation.isPending && deleteWallMutation.variables === wall.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
