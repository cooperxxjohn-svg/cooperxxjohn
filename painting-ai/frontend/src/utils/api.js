import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Projects
export const getProjects = async () => {
  const response = await api.get('/projects')
  return response.data
}

export const getProject = async (projectId) => {
  const response = await api.get(`/projects/${projectId}`)
  return response.data
}

export const createProject = async (data) => {
  const response = await api.post('/projects', data)
  return response.data
}

export const uploadDrawing = async (projectId, file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post(`/projects/${projectId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export const getProjectRooms = async (projectId) => {
  const response = await api.get(`/projects/${projectId}/rooms`)
  return response.data
}

export const generateEstimate = async (projectId, params) => {
  const response = await api.post(`/projects/${projectId}/estimate`, params)
  return response.data
}

export default api
