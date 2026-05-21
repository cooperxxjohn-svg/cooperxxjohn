import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Upload as UploadIcon, File, X, Loader2, AlertCircle, CheckCircle } from 'lucide-react'
import { createProject, uploadDrawing } from '../utils/api'

export default function Upload() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [projectData, setProjectData] = useState({
    name: '',
    customer: '',
    address: '',
  })
  const [dragActive, setDragActive] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(null)

  const createProjectMutation = useMutation({
    mutationFn: createProject,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ projectId, file }) => uploadDrawing(projectId, file),
    onSuccess: (data, variables) => {
      setUploadProgress({ status: 'complete', message: 'Processing complete!' })
      setTimeout(() => {
        navigate(`/dashboard/projects/${variables.projectId}`)
      }, 1500)
    },
  })

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files[0]) {
      validateAndSetFile(files[0])
    }
  }, [])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (file) => {
    const maxSize = 50 * 1024 * 1024 // 50MB
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg']

    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PDF, PNG, or JPG file')
      return
    }

    if (file.size > maxSize) {
      alert('File size must be less than 50MB')
      return
    }

    setFile(file)
  }

  const handleRemoveFile = () => {
    setFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file || !projectData.name) {
      alert('Please provide a project name and upload a file')
      return
    }

    try {
      setUploadProgress({ status: 'uploading', message: 'Creating project...' })

      const project = await createProjectMutation.mutateAsync({
        name: projectData.name,
        customer: projectData.customer,
        address: projectData.address,
      })

      setUploadProgress({ status: 'uploading', message: 'Uploading drawing...' })

      await uploadMutation.mutateAsync({
        projectId: project.id,
        file: file,
      })
    } catch (error) {
      setUploadProgress(null)
      // Error is already handled by React Query error state
    }
  }

  const isSubmitting = createProjectMutation.isPending || uploadMutation.isPending

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Floor Plan</h1>
        <p className="text-gray-600 mt-2">
          Upload a PDF or image of your floor plan to get started
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Project Details */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Details</h2>

          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Project Name *
              </label>
              <input
                type="text"
                id="name"
                required
                value={projectData.name}
                onChange={(e) => setProjectData({ ...projectData, name: e.target.value })}
                className="input"
                placeholder="Downtown Office Renovation"
              />
            </div>

            <div>
              <label htmlFor="customer" className="block text-sm font-medium text-gray-700 mb-2">
                Customer Name
              </label>
              <input
                type="text"
                id="customer"
                value={projectData.customer}
                onChange={(e) => setProjectData({ ...projectData, customer: e.target.value })}
                className="input"
                placeholder="ABC Commercial Properties"
              />
            </div>

            <div>
              <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                Address
              </label>
              <input
                type="text"
                id="address"
                value={projectData.address}
                onChange={(e) => setProjectData({ ...projectData, address: e.target.value })}
                className="input"
                placeholder="123 Main St, San Francisco, CA"
              />
            </div>
          </div>
        </div>

        {/* File Upload */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Floor Plan</h2>

          {!file ? (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <UploadIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-700 font-medium mb-2">
                Drop your floor plan here, or{' '}
                <label htmlFor="file-upload" className="text-primary-600 hover:text-primary-700 cursor-pointer">
                  browse
                </label>
              </p>
              <p className="text-sm text-gray-500">
                PDF, PNG, or JPG up to 50MB
              </p>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="border rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                  <File className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleRemoveFile}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {uploadProgress && (
          <div className={`card ${
            uploadProgress.status === 'complete' ? 'bg-green-50 border-green-200' : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center space-x-3">
              {uploadProgress.status === 'complete' ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
              )}
              <div>
                <p className={`font-medium ${
                  uploadProgress.status === 'complete' ? 'text-green-900' : 'text-blue-900'
                }`}>
                  {uploadProgress.message}
                </p>
                {uploadProgress.status !== 'complete' && (
                  <p className="text-sm text-blue-700 mt-1">
                    This may take a minute...
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {(createProjectMutation.isError || uploadMutation.isError) && (
          <div className="card bg-red-50 border-red-200">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-red-900">Upload failed</p>
                <p className="text-sm text-red-700 mt-1">
                  {createProjectMutation.error?.response?.data?.detail ||
                   uploadMutation.error?.response?.data?.detail ||
                   'Please try again'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="btn btn-secondary"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary flex items-center space-x-2"
            disabled={isSubmitting || !file}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <UploadIcon className="w-4 h-4" />
                <span>Upload & Process</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
