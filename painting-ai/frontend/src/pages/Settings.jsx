import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Key, Bell, CreditCard, Users, Save, Loader2 } from 'lucide-react';
import useAuthStore from '../store/authStore';
import api from '../utils/api';

export default function Settings() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('profile');
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (data) => {
      const response = await api.put('/users/me', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['user']);
      alert('Profile updated successfully!');
    },
  });

  const handleProfileSave = () => {
    updateProfileMutation.mutate(profileData);
  };

  const handleBillingPortal = async () => {
    try {
      const response = await api.post('/checkout/portal', {
        return_url: window.location.origin + '/dashboard/settings?tab=billing',
      });
      window.location.href = response.data.portal_url;
    } catch (error) {
      alert('Failed to open billing portal: ' + error.response?.data?.detail);
    }
  };

  const tabs = [
    { id: 'profile', name: 'Profile', icon: User },
    { id: 'api', name: 'API Keys', icon: Key },
    { id: 'notifications', name: 'Notifications', icon: Bell },
    { id: 'billing', name: 'Billing', icon: CreditCard },
    { id: 'team', name: 'Team', icon: Users },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Manage your account and preferences</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar */}
        <div className="col-span-3">
          <nav className="space-y-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="col-span-9">
          <div className="card">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile Settings</h2>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={profileData.name}
                      onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                      className="input"
                      placeholder="John Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="input"
                      placeholder="you@example.com"
                    />
                  </div>

                  <div className="pt-4 border-t">
                    <button
                      onClick={handleProfileSave}
                      disabled={updateProfileMutation.isPending}
                      className="btn btn-primary flex items-center space-x-2"
                    >
                      {updateProfileMutation.isPending ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          <span>Save Changes</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">API Keys</h2>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-800">
                    Your API key allows you to access the Drywall.ai API programmatically.
                    Keep it secret and never commit it to version control.
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API Key
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="password"
                        value={user?.api_key || ''}
                        readOnly
                        className="input flex-1 font-mono text-sm"
                      />
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(user?.api_key || '');
                          alert('API key copied to clipboard!');
                        }}
                        className="btn btn-secondary"
                      >
                        Copy
                      </button>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Usage Example</h3>
                    <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto">
{`curl -X POST https://api.drywall.ai/api/projects \\
  -H "X-API-Key: ${user?.api_key || 'your_api_key'}" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "My Project"}'`}
                    </pre>
                  </div>

                  <div>
                    <a
                      href="/docs/api"
                      className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    >
                      View API Documentation →
                    </a>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Notification Preferences</h2>

                <div className="space-y-4">
                  <div className="flex items-center justify-between py-3 border-b">
                    <div>
                      <p className="font-medium text-gray-900">Project Completed</p>
                      <p className="text-sm text-gray-600">When AI processing finishes</p>
                    </div>
                    <input type="checkbox" defaultChecked className="toggle" />
                  </div>

                  <div className="flex items-center justify-between py-3 border-b">
                    <div>
                      <p className="font-medium text-gray-900">Export Ready</p>
                      <p className="text-sm text-gray-600">When Excel/PDF is generated</p>
                    </div>
                    <input type="checkbox" defaultChecked className="toggle" />
                  </div>

                  <div className="flex items-center justify-between py-3 border-b">
                    <div>
                      <p className="font-medium text-gray-900">Payment Notifications</p>
                      <p className="text-sm text-gray-600">Receipts and payment updates</p>
                    </div>
                    <input type="checkbox" defaultChecked className="toggle" />
                  </div>

                  <div className="flex items-center justify-between py-3 border-b">
                    <div>
                      <p className="font-medium text-gray-900">Marketing Emails</p>
                      <p className="text-sm text-gray-600">Product updates and tips</p>
                    </div>
                    <input type="checkbox" className="toggle" />
                  </div>
                </div>
              </div>
            )}

            {/* Billing Tab */}
            {activeTab === 'billing' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Billing & Subscription</h2>

                <div className="space-y-6">
                  <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-6 border border-primary-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Current Plan</p>
                        <p className="text-2xl font-bold text-gray-900 mt-1">
                          {user?.plan || 'Free'}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          Status: <span className="font-medium">{user?.subscription_status || 'inactive'}</span>
                        </p>
                      </div>
                      <button
                        onClick={handleBillingPortal}
                        className="btn btn-primary"
                      >
                        Manage Subscription
                      </button>
                    </div>
                  </div>

                  {user?.plan === 'trial' && user?.settings?.trial_ends && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-sm text-yellow-800">
                        <strong>Trial ends:</strong> {new Date(user.settings.trial_ends).toLocaleDateString()}
                      </p>
                      <a href="/pricing" className="text-sm font-medium text-yellow-900 hover:text-yellow-700 mt-2 inline-block">
                        Upgrade now →
                      </a>
                    </div>
                  )}

                  <div>
                    <h3 className="font-medium text-gray-900 mb-4">Billing Portal</h3>
                    <p className="text-sm text-gray-600 mb-4">
                      In the billing portal you can:
                    </p>
                    <ul className="text-sm text-gray-600 space-y-2">
                      <li>• Update payment method</li>
                      <li>• View invoices and payment history</li>
                      <li>• Download receipts</li>
                      <li>• Cancel subscription</li>
                      <li>• Update billing information</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Team Tab */}
            {activeTab === 'team' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Team Members</h2>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-blue-800">
                    Team collaboration requires a Pro or Enterprise plan.
                  </p>
                  <a href="/pricing" className="text-sm font-medium text-blue-900 hover:text-blue-700 mt-2 inline-block">
                    Upgrade to Pro →
                  </a>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Invite Team Member
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="email"
                        placeholder="email@example.com"
                        className="input flex-1"
                        disabled={user?.plan === 'trial' || user?.plan === 'starter'}
                      />
                      <button
                        className="btn btn-primary"
                        disabled={user?.plan === 'trial' || user?.plan === 'starter'}
                      >
                        Invite
                      </button>
                    </div>
                  </div>

                  <div className="text-sm text-gray-600">
                    <p>Team member limit: {user?.plan === 'pro' ? '5 members' : '1 member (you)'}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
