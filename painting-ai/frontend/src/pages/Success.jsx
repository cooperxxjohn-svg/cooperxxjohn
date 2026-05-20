import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, ArrowRight, Download, Loader2 } from 'lucide-react';
import useAuthStore from '../store/authStore';
import api from '../utils/api';

export default function Success() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const user = useAuthStore((state) => state.user);
  const [loading, setLoading] = useState(true);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');

    if (!sessionId) {
      navigate('/pricing');
      return;
    }

    // Verify the session and get subscription details
    const verifySession = async () => {
      try {
        const response = await api.get(`/checkout/session/${sessionId}`);
        setSubscriptionDetails(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to verify session:', error);
        setLoading(false);
      }
    };

    verifySession();
  }, [searchParams, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Confirming your subscription...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Success Message */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-green-500 to-green-600 p-8 text-center">
            <CheckCircle className="w-16 h-16 text-white mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome to Painting.ai!
            </h1>
            <p className="text-green-100 text-lg">
              Your subscription is now active
            </p>
          </div>

          <div className="p-8">
            {/* Subscription Details */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Subscription Details
              </h2>
              <div className="bg-gray-50 rounded-lg p-6 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Plan:</span>
                  <span className="font-medium text-gray-900 capitalize">
                    {subscriptionDetails?.plan || user?.plan || 'Pro'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium text-green-600">Active</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Trial Period:</span>
                  <span className="font-medium text-gray-900">14 days free</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Billing Starts:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Next Steps */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                What's Next?
              </h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-primary-700 font-semibold">1</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Upload Your First Floor Plan</h3>
                    <p className="text-sm text-gray-600">
                      Start by uploading a PDF or image of your project floor plan
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-primary-700 font-semibold">2</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Review AI Detections</h3>
                    <p className="text-sm text-gray-600">
                      Our AI will detect rooms automatically - you can review and edit
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-primary-700 font-semibold">3</span>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Generate Professional Estimates</h3>
                    <p className="text-sm text-gray-600">
                      Download detailed Excel spreadsheets and PDF proposals
                    </p>
                  </div>
                </div>

                {subscriptionDetails?.plan === 'pro' && (
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-primary-700 font-semibold">4</span>
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Access the API</h3>
                      <p className="text-sm text-gray-600">
                        Integrate Painting.ai into your existing workflow with our API
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Pro Features Highlight */}
            {subscriptionDetails?.plan === 'pro' && (
              <div className="mb-8 bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-6 border border-primary-100">
                <h3 className="font-semibold text-gray-900 mb-3">
                  🎉 Pro Features Unlocked
                </h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    Unlimited projects per month
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    Assembly expansion (80-120 line items)
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    Public API access with webhooks
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    Priority support (response within 4 hours)
                  </li>
                  <li className="flex items-center">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    Team collaboration (up to 5 members)
                  </li>
                </ul>
              </div>
            )}

            {/* Quick Actions */}
            <div className="space-y-3">
              <button
                onClick={() => navigate('/dashboard/upload')}
                className="w-full btn btn-primary flex items-center justify-center space-x-2"
              >
                <span>Upload Your First Project</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                className="w-full btn btn-secondary flex items-center justify-center space-x-2"
              >
                <span>Go to Dashboard</span>
              </button>

              {subscriptionDetails?.plan === 'pro' && (
                <button
                  onClick={() => navigate('/dashboard/settings?tab=api')}
                  className="w-full btn btn-secondary flex items-center justify-center space-x-2"
                >
                  <span>View API Keys</span>
                </button>
              )}
            </div>

            {/* Receipt Link */}
            <div className="mt-6 pt-6 border-t text-center">
              <p className="text-sm text-gray-600 mb-2">
                A confirmation email with your receipt has been sent to{' '}
                <span className="font-medium">{user?.email}</span>
              </p>
              <button
                onClick={() => navigate('/settings?tab=billing')}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium inline-flex items-center"
              >
                <Download className="w-4 h-4 mr-1" />
                Download Invoice
              </button>
            </div>
          </div>
        </div>

        {/* Support Card */}
        <div className="mt-6 bg-white rounded-lg shadow p-6 text-center">
          <h3 className="font-semibold text-gray-900 mb-2">
            Need Help Getting Started?
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Our team is here to help you get the most out of Painting.ai
          </p>
          <div className="flex justify-center space-x-4">
            <a
              href="/docs"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View Documentation
            </a>
            <span className="text-gray-300">|</span>
            <a
              href="mailto:support@painting.ai"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Contact Support
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
