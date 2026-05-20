import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, Search } from 'lucide-react';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        {/* 404 Illustration */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-200">404</h1>
          <div className="relative -mt-12">
            <Search className="w-24 h-24 text-gray-400 mx-auto" />
          </div>
        </div>

        {/* Error Message */}
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Page Not Found
        </h2>
        <p className="text-gray-600 mb-8">
          Sorry, we couldn't find the page you're looking for.
          It might have been moved or deleted.
        </p>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate(-1)}
            className="w-full btn btn-secondary flex items-center justify-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </button>

          <button
            onClick={() => navigate('/')}
            className="w-full btn btn-primary flex items-center justify-center space-x-2"
          >
            <Home className="w-4 h-4" />
            <span>Go to Dashboard</span>
          </button>
        </div>

        {/* Helpful Links */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-4">Looking for something?</p>
          <div className="flex justify-center space-x-6 text-sm">
            <button
              onClick={() => navigate('/upload')}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Upload Project
            </button>
            <button
              onClick={() => navigate('/settings')}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Settings
            </button>
            <button
              onClick={() => navigate('/pricing')}
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              Pricing
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
