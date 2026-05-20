import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Upload, Loader2, CheckCircle } from 'lucide-react'
import { createProject, uploadDrawing } from '../utils/api'

export default function NewProject() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [projectData, setProjectData] = useState({
    name: '',
    customer: '',
  })
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (data) => {
      setStep(2)
      setProjectData((prev) => ({ ...prev, id: data.id }))
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (step === 1) {
      createProjectMutation.mutate(projectData)
    } else if (step === 2 && file) {
      setUploading(true)
      try {
        await uploadDrawing(projectData.id, file)
        setStep(3)
        // Redirect to project after 2 seconds
        setTimeout(() => {
          navigate(`/projects/${projectData.id}`)
        }, 2000)
      } catch (error) {
        console.error('Upload failed:', error)
        alert('Failed to upload drawing. Please try again.')
      } finally {
        setUploading(false)
      }
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Create New Project</h1>
        <p className="text-gray-600 mt-2">Upload drawings and generate AI-powered takeoffs</p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  step >= i
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step > i ? <CheckCircle className="w-6 h-6" /> : i}
              </div>
              {i < 3 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    step > i ? 'bg-primary-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={step >= 1 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
            Project Info
          </span>
          <span className={step >= 2 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
            Upload Drawings
          </span>
          <span className={step >= 3 ? 'text-gray-900 font-medium' : 'text-gray-500'}>
            Processing
          </span>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name *
                </label>
                <input
                  type="text"
                  required
                  className="input"
                  placeholder="Office Renovation"
                  value={projectData.name}
                  onChange={(e) =>
                    setProjectData({ ...projectData, name: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Customer Name (Optional)
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="ABC Construction"
                  value={projectData.customer}
                  onChange={(e) =>
                    setProjectData({ ...projectData, customer: e.target.value })
                  }
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full"
                disabled={createProjectMutation.isPending}
              >
                {createProjectMutation.isPending ? (
                  <span className="flex items-center justify-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </span>
                ) : (
                  'Continue'
                )}
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Drawing (PDF, PNG, JPG)
                </label>

                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  {!file ? (
                    <div>
                      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600 mb-2">
                        Drag and drop your drawing here, or click to browse
                      </p>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={handleFileChange}
                        className="hidden"
                        id="file-upload"
                      />
                      <label
                        htmlFor="file-upload"
                        className="btn btn-secondary cursor-pointer inline-block"
                      >
                        Choose File
                      </label>
                    </div>
                  ) : (
                    <div>
                      <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                      <p className="text-gray-900 font-medium">{file.name}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <button
                        type="button"
                        onClick={() => setFile(null)}
                        className="text-sm text-primary-600 hover:underline mt-2"
                      >
                        Change file
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full"
                disabled={!file || uploading}
              >
                {uploading ? (
                  <span className="flex items-center justify-center">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </span>
                ) : (
                  'Upload & Process'
                )}
              </button>
            </div>
          )}

          {step === 3 && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-10 h-10 text-green-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Processing Your Drawing
              </h2>
              <p className="text-gray-600 mb-4">
                Our AI is analyzing the drawing and extracting room dimensions...
              </p>
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                <span className="text-sm text-gray-600">
                  Redirecting to project...
                </span>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
