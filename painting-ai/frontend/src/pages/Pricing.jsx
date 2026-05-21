import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Zap } from 'lucide-react';
import useAuthStore from '../store/authStore';
import api from '../utils/api';

export default function Pricing() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [loading, setLoading] = useState(null);

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: 99,
      description: 'Perfect for solo contractors',
      features: [
        '50 takeoffs per month',
        'AI wall & opening detection',
        'Excel & PDF exports',
        'Email support',
        '1 user',
      ],
    },
    {
      id: 'pro',
      name: 'Pro',
      price: 299,
      description: 'For growing businesses',
      popular: true,
      features: [
        'Unlimited takeoffs',
        'AI wall & opening detection',
        'Material & labor breakdown',
        'Excel & PDF exports',
        'Public API access',
        'Priority support',
        'Custom materials database',
        'Up to 5 team members',
      ],
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: null,
      description: 'For large organizations',
      features: [
        'Everything in Pro',
        'Unlimited team members',
        'White-label exports',
        'Custom integrations',
        'Dedicated account manager',
        'SLA guarantee',
        'Custom training',
        'Volume discounts',
      ],
    },
  ];

  const handleSubscribe = async (planId) => {
    if (!isAuthenticated) {
      navigate('/register');
      return;
    }

    if (planId === 'enterprise') {
      window.location.href = 'mailto:sales@drywall.ai?subject=Enterprise Plan Inquiry';
      return;
    }

    setLoading(planId);

    try {
      const response = await api.post('/checkout/create-session', {
        plan: planId,
        success_url: window.location.origin + '/success',
        cancel_url: window.location.origin + '/pricing',
      });

      window.location.href = response.data.checkout_url;
    } catch (error) {
      alert('Checkout failed: ' + (error.response?.data?.detail || 'Please try again'));
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600">
            Choose the plan that's right for your business
          </p>
          <div className="mt-4 inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-2 rounded-full">
            <Zap className="w-4 h-4" />
            <span className="text-sm font-medium">14-day free trial on all plans</span>
          </div>
        </div>

        {/* Plans */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-lg shadow-lg overflow-hidden ${
                plan.popular ? 'ring-2 ring-primary-500 relative' : ''
              }`}
            >
              {plan.popular && (
                <div className="bg-primary-500 text-white text-center py-2 text-sm font-medium">
                  Most Popular
                </div>
              )}

              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <p className="text-gray-600 mb-6">{plan.description}</p>

                <div className="mb-6">
                  {plan.price ? (
                    <>
                      <span className="text-5xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-600">/month</span>
                    </>
                  ) : (
                    <span className="text-3xl font-bold text-gray-900">Custom</span>
                  )}
                </div>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={loading === plan.id}
                  className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
                    plan.popular
                      ? 'bg-primary-600 text-white hover:bg-primary-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  } ${loading === plan.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {loading === plan.id
                    ? 'Loading...'
                    : plan.price
                    ? 'Start Free Trial'
                    : 'Contact Sales'}
                </button>

                <ul className="mt-8 space-y-4">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            <div className="bg-white rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                What's included in the free trial?
              </h3>
              <p className="text-gray-600">
                All plans include a 14-day free trial with full access to all features.
                No credit card required to start. You'll only be charged after the trial ends.
              </p>
            </div>

            <div className="bg-white rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                Can I change plans later?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade your plan at any time from your settings.
                Changes take effect immediately, and we'll prorate your billing.
              </p>
            </div>

            <div className="bg-white rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit cards (Visa, Mastercard, American Express, Discover)
                through our secure payment processor, Stripe.
              </p>
            </div>

            <div className="bg-white rounded-lg p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                Can I cancel anytime?
              </h3>
              <p className="text-gray-600">
                Absolutely. You can cancel your subscription at any time with no penalties.
                You'll retain access until the end of your billing period.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
