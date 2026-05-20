import { useNavigate } from 'react-router-dom';
import { PaintBucket, Zap, Check, ArrowRight, Upload, FileText, Download, Users } from 'lucide-react';
import useAuthStore from '../store/authStore';

export default function Landing() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/');
    } else {
      navigate('/register');
    }
  };

  const features = [
    {
      icon: Upload,
      title: 'Upload Floor Plans',
      description: 'Drag and drop PDF or image files. Our AI processes them in under 60 seconds.',
    },
    {
      icon: Zap,
      title: 'AI-Powered Detection',
      description: 'Automatically detect rooms, calculate square footage, and identify surfaces.',
    },
    {
      icon: FileText,
      title: 'Detailed Estimates',
      description: 'Generate professional estimates with 80-120 line items per room using assembly expansion.',
    },
    {
      icon: Download,
      title: 'Professional Exports',
      description: 'Download Excel spreadsheets and PDF proposals with your company branding.',
    },
  ];

  const steps = [
    {
      number: '1',
      title: 'Upload Your Floor Plan',
      description: 'Simply drag and drop a PDF or image of your project floor plan.',
    },
    {
      number: '2',
      title: 'Review AI Detections',
      description: 'Our AI detects rooms automatically. Review, edit, and refine as needed.',
    },
    {
      number: '3',
      title: 'Generate Estimate',
      description: 'Expand into detailed line items with material costs and labor hours.',
    },
    {
      number: '4',
      title: 'Export & Win',
      description: 'Download professional proposals and send to clients instantly.',
    },
  ];

  const testimonials = [
    {
      name: 'Mike Johnson',
      company: 'Johnson Painting Co.',
      text: 'Cut my estimating time from 3 hours to 15 minutes. This is a game-changer.',
      rating: 5,
    },
    {
      name: 'Sarah Williams',
      company: 'Elite Contractors',
      text: 'The detailed breakdowns help me win more bids. Clients love the transparency.',
      rating: 5,
    },
    {
      name: 'David Chen',
      company: 'Pro Paint Solutions',
      text: 'Paid for itself in the first week. Best investment I\'ve made for my business.',
      rating: 5,
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <PaintBucket className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Painting.ai</span>
            </div>

            <div className="flex items-center space-x-4">
              <a href="/pricing" className="text-gray-600 hover:text-gray-900 font-medium">
                Pricing
              </a>
              <a href="/help" className="text-gray-600 hover:text-gray-900 font-medium">
                Help
              </a>
              {isAuthenticated ? (
                <button
                  onClick={() => navigate('/')}
                  className="btn btn-primary"
                >
                  Dashboard
                </button>
              ) : (
                <>
                  <button
                    onClick={() => navigate('/login')}
                    className="text-gray-600 hover:text-gray-900 font-medium"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => navigate('/register')}
                    className="btn btn-primary"
                  >
                    Start Free Trial
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 bg-gradient-to-br from-primary-50 to-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              AI-Powered Estimates for
              <br />
              <span className="text-primary-600">Painting Contractors</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Upload a floor plan, get a detailed estimate in minutes. No more manual takeoffs.
              No more spreadsheet headaches. Just upload, review, and win bids.
            </p>

            <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4 mb-8">
              <button
                onClick={handleGetStarted}
                className="btn btn-primary btn-lg flex items-center space-x-2"
              >
                <span>Start Free Trial</span>
                <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => navigate('/pricing')}
                className="btn btn-secondary btn-lg"
              >
                View Pricing
              </button>
            </div>

            <p className="text-sm text-gray-600">
              14-day free trial • No credit card required • Cancel anytime
            </p>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">95%+</p>
              <p className="text-gray-600 mt-2">AI Accuracy</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">&lt;60s</p>
              <p className="text-gray-600 mt-2">Processing Time</p>
            </div>
            <div className="text-center">
              <p className="text-4xl font-bold text-primary-600">80-120</p>
              <p className="text-gray-600 mt-2">Line Items Per Room</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Win More Bids
            </h2>
            <p className="text-xl text-gray-600">
              Powerful features designed for painting contractors
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="text-center">
                  <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Icon className="w-8 h-8 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              From upload to estimate in 4 simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <div className="bg-white rounded-lg p-6 shadow-lg">
                  <div className="w-12 h-12 bg-primary-600 rounded-full flex items-center justify-center mb-4">
                    <span className="text-2xl font-bold text-white">{step.number}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {step.title}
                  </h3>
                  <p className="text-gray-600">{step.description}</p>
                </div>
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                    <ArrowRight className="w-8 h-8 text-gray-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Trusted by Painting Contractors
            </h2>
            <p className="text-xl text-gray-600">
              See what our customers have to say
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <svg
                      key={i}
                      className="w-5 h-5 text-yellow-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-600 mb-4 italic">"{testimonial.text}"</p>
                <div>
                  <p className="font-semibold text-gray-900">{testimonial.name}</p>
                  <p className="text-sm text-gray-600">{testimonial.company}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-primary-600 to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Estimating Process?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join hundreds of contractors who save hours every week with Painting.ai
          </p>
          <button
            onClick={handleGetStarted}
            className="bg-white text-primary-600 hover:bg-gray-100 px-8 py-4 rounded-lg font-semibold text-lg flex items-center space-x-2 mx-auto"
          >
            <span>Start Your Free Trial</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          <p className="text-primary-100 mt-4 text-sm">
            14 days free • No credit card required
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <PaintBucket className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">Painting.ai</span>
              </div>
              <p className="text-sm">
                AI-powered takeoffs for painting contractors
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/pricing" className="hover:text-white">Pricing</a></li>
                <li><a href="/help" className="hover:text-white">Help</a></li>
                <li><a href="/docs" className="hover:text-white">Documentation</a></li>
                <li><a href="/docs/api" className="hover:text-white">API</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/about" className="hover:text-white">About</a></li>
                <li><a href="mailto:support@painting.ai" className="hover:text-white">Contact</a></li>
                <li><a href="/terms" className="hover:text-white">Terms</a></li>
                <li><a href="/privacy" className="hover:text-white">Privacy</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-4">Connect</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="mailto:support@painting.ai" className="hover:text-white">support@painting.ai</a></li>
                <li><a href="mailto:sales@painting.ai" className="hover:text-white">sales@painting.ai</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 pt-8 text-center text-sm">
            <p>&copy; 2026 Painting.ai Inc. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
