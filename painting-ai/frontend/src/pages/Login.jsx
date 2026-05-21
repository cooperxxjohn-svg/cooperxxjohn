import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Loader2, AlertCircle, Hammer } from 'lucide-react'
import { login } from '../utils/api'
import useAuthStore from '../store/authStore'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuth(data.user, data.access_token, data.refresh_token)
      navigate('/')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    loginMutation.mutate(formData)
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <Hammer className="w-12 h-12 text-primary-600" />
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          Sign in to Drywall.ai
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Or{' '}
          <Link to="/register" className="font-medium text-primary-600 hover:text-primary-500">
            create a new account
          </Link>
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {loginMutation.isError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                <div className="text-sm text-red-800">
                  {loginMutation.error?.response?.data?.detail || 'Failed to sign in'}
                </div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="input"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <a href="#" className="font-medium text-primary-600 hover:text-primary-500">
                  Forgot password?
                </a>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loginMutation.isPending}
                className="w-full btn btn-primary flex items-center justify-center"
              >
                {loginMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Demo credentials</span>
              </div>
            </div>

            <div className="mt-4 bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
              <p className="font-medium mb-1">For testing:</p>
              <p>Email: demo@drywall.ai</p>
              <p>Password: demo123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
