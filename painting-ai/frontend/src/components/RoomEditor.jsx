import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Edit2, Trash2, Plus, Save, X, Loader2 } from 'lucide-react'
import api from '../utils/api'

export default function RoomEditor({ projectId, rooms = [] }) {
  const queryClient = useQueryClient()
  const [editingRoom, setEditingRoom] = useState(null)
  const [addingRoom, setAddingRoom] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    dimensions: { length: 0, width: 0, height: 0 },
    notes: '',
  })

  const updateRoomMutation = useMutation({
    mutationFn: async ({ roomId, updates }) => {
      const response = await api.put(`/projects/${projectId}/rooms/${roomId}`, updates)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
      setEditingRoom(null)
    },
  })

  const deleteRoomMutation = useMutation({
    mutationFn: async (roomId) => {
      const response = await api.delete(`/projects/${projectId}/rooms/${roomId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
    },
  })

  const addRoomMutation = useMutation({
    mutationFn: async (roomData) => {
      const response = await api.post(`/projects/${projectId}/rooms`, roomData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['rooms', projectId])
      queryClient.invalidateQueries(['project', projectId])
      setAddingRoom(false)
      setFormData({
        name: '',
        dimensions: { length: 0, width: 0, height: 0 },
        notes: '',
      })
    },
  })

  const handleEdit = (room) => {
    setEditingRoom(room.id)
    setFormData({
      name: room.name,
      dimensions: room.dimensions || { length: 0, width: 0, height: 0 },
      notes: room.notes || '',
    })
  }

  const handleSave = (roomId) => {
    updateRoomMutation.mutate({ roomId, updates: formData })
  }

  const handleDelete = (roomId) => {
    if (confirm('Are you sure you want to delete this room?')) {
      deleteRoomMutation.mutate(roomId)
    }
  }

  const handleAddRoom = () => {
    addRoomMutation.mutate(formData)
  }

  const handleCancel = () => {
    setEditingRoom(null)
    setAddingRoom(false)
    setFormData({
      name: '',
      dimensions: { length: 0, width: 0, height: 0 },
      notes: '',
    })
  }

  const calculateArea = (dimensions) => {
    if (!dimensions) return 0
    const { length, width, height } = dimensions
    const walls = 2 * (length + width) * height
    const ceiling = length * width
    return walls + ceiling
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Rooms ({rooms.length})
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Review AI detections and make corrections
          </p>
        </div>
        <button
          onClick={() => setAddingRoom(true)}
          className="btn btn-secondary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Room</span>
        </button>
      </div>

      {/* Add Room Form */}
      {addingRoom && (
        <div className="card bg-blue-50 border-blue-200">
          <h3 className="font-semibold text-gray-900 mb-4">Add New Room</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Room Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
                placeholder="Conference Room"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Length (ft)
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
                  Width (ft)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.dimensions.width}
                  onChange={(e) => setFormData({
                    ...formData,
                    dimensions: { ...formData.dimensions, width: parseFloat(e.target.value) || 0 }
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
                onClick={handleAddRoom}
                disabled={addRoomMutation.isPending || !formData.name}
                className="btn btn-primary flex items-center space-x-2"
              >
                {addRoomMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Adding...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Add Room</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rooms List */}
      {rooms.length === 0 && !addingRoom ? (
        <div className="text-center py-8 text-gray-500">
          <p>No rooms detected yet</p>
          <p className="text-sm mt-1">Upload a floor plan to get started</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rooms.map((room) => (
            <div key={room.id} className="border rounded-lg p-4">
              {editingRoom === room.id ? (
                // Edit Mode
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Room Name
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Length (ft)
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
                        Width (ft)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={formData.dimensions.width}
                        onChange={(e) => setFormData({
                          ...formData,
                          dimensions: { ...formData.dimensions, width: parseFloat(e.target.value) || 0 }
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
                      onClick={() => handleSave(room.id)}
                      disabled={updateRoomMutation.isPending}
                      className="btn btn-primary flex items-center space-x-2"
                    >
                      {updateRoomMutation.isPending ? (
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
                    <h3 className="font-semibold text-gray-900">{room.name}</h3>
                    {room.dimensions && (
                      <p className="text-sm text-gray-600 mt-1">
                        {room.dimensions.length}' × {room.dimensions.width}' × {room.dimensions.height}'
                      </p>
                    )}
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Total Area: </span>
                      <span className="font-medium text-gray-900">
                        {room.total_area || calculateArea(room.dimensions)} sqft
                      </span>
                    </div>
                    {room.notes && (
                      <p className="text-sm text-gray-600 mt-2">{room.notes}</p>
                    )}
                  </div>

                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => handleEdit(room)}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-gray-100 rounded"
                      title="Edit room"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(room.id)}
                      disabled={deleteRoomMutation.isPending}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Delete room"
                    >
                      {deleteRoomMutation.isPending && deleteRoomMutation.variables === room.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Surfaces breakdown */}
              {!editingRoom && room.surfaces && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t">
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
  )
}
