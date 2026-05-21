import { useState } from 'react';
import { Search, ChevronDown, ChevronUp, Book, MessageCircle, Mail, FileText } from 'lucide-react';

export default function Help() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFaq, setExpandedFaq] = useState(null);

  const faqs = [
    {
      category: 'Getting Started',
      questions: [
        {
          id: 1,
          question: 'How do I upload a floor plan?',
          answer: 'Click the "New Takeoff" button in the top navigation, then drag and drop your PDF or image file (PNG, JPG). Files up to 50MB are supported. The AI will automatically detect walls and calculate material quantities within 60 seconds.',
        },
        {
          id: 2,
          question: 'What file formats are supported?',
          answer: 'We support PDF, PNG, and JPG files up to 50MB. For best results, use clear, high-resolution floor plans with visible wall boundaries and dimensions.',
        },
        {
          id: 3,
          question: 'How accurate is the AI detection?',
          answer: 'Our AI achieves 95%+ accuracy on standard floor plans. You can always review and edit detected walls, dimensions, and measurements before generating your final takeoff.',
        },
      ],
    },
    {
      category: 'Projects & Estimates',
      questions: [
        {
          id: 4,
          question: 'Can I edit AI-detected walls?',
          answer: 'Yes! After upload, you\'ll see a wall review interface where you can edit wall names, linear footage, heights, openings, and wall type (interior/exterior). You can also add manual walls or delete incorrect detections.',
        },
        {
          id: 5,
          question: 'What is Material Breakdown?',
          answer: 'Our system provides a complete material list including studs, drywall sheets, joint compound, tape, corner bead, screws, and labor hours broken down by phase: Framing, Hanging, Taping, Mudding, Sanding, and Finishing.',
        },
        {
          id: 6,
          question: 'How do I export my takeoff?',
          answer: 'Once your project is processed, click "Export to Excel" for a detailed spreadsheet or "Export to PDF" for a professional proposal with your company branding.',
        },
      ],
    },
    {
      category: 'Billing & Subscriptions',
      questions: [
        {
          id: 7,
          question: 'What plans are available?',
          answer: 'We offer three plans: Starter ($99/mo) for solo contractors with 50 takeoffs/month, Pro ($299/mo) for unlimited takeoffs + API access + team features, and Enterprise (custom pricing) for large organizations with white-label needs.',
        },
        {
          id: 8,
          question: 'Is there a free trial?',
          answer: 'Yes! All plans include a 14-day free trial with full access to all features. No credit card required to start. You\'ll only be charged after the trial ends.',
        },
        {
          id: 9,
          question: 'How do I cancel my subscription?',
          answer: 'Go to Settings → Billing → Manage Subscription. You can cancel anytime with no penalties. You\'ll retain access until the end of your billing period.',
        },
      ],
    },
    {
      category: 'API & Integrations',
      questions: [
        {
          id: 10,
          question: 'How do I access the API?',
          answer: 'API access is available on Pro and Enterprise plans. Go to Settings → API Keys to view your key and documentation. The API allows you to upload projects, retrieve estimates, and receive webhook notifications programmatically.',
        },
        {
          id: 11,
          question: 'What are webhooks?',
          answer: 'Webhooks notify your systems when events occur (e.g., project completed, export generated). Configure them via the API or contact support for assistance.',
        },
        {
          id: 12,
          question: 'Can I integrate with QuickBooks/other tools?',
          answer: 'Enterprise plans include custom integrations. Contact our sales team to discuss your specific integration needs.',
        },
      ],
    },
  ];

  const filteredFaqs = faqs.map((category) => ({
    ...category,
    questions: category.questions.filter((q) =>
      searchQuery === '' ||
      q.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.answer.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((category) => category.questions.length > 0);

  const toggleFaq = (id) => {
    setExpandedFaq(expandedFaq === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            How can we help you?
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Find answers to common questions and learn how to use Drywall.ai
          </p>

          {/* Search */}
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search help articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-12 w-full"
              />
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <a
            href="/docs"
            className="bg-white rounded-lg p-6 shadow hover:shadow-lg transition-shadow"
          >
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <Book className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Documentation</h3>
            <p className="text-sm text-gray-600">
              Complete guides and tutorials for using Drywall.ai
            </p>
          </a>

          <a
            href="/docs/api"
            className="bg-white rounded-lg p-6 shadow hover:shadow-lg transition-shadow"
          >
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <FileText className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">API Reference</h3>
            <p className="text-sm text-gray-600">
              Technical documentation for developers
            </p>
          </a>

          <a
            href="mailto:support@drywall.ai"
            className="bg-white rounded-lg p-6 shadow hover:shadow-lg transition-shadow"
          >
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
              <Mail className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Contact Support</h3>
            <p className="text-sm text-gray-600">
              Get help from our support team
            </p>
          </a>
        </div>

        {/* FAQs */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-bold text-gray-900">
              Frequently Asked Questions
            </h2>
          </div>

          {filteredFaqs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-600">No results found for "{searchQuery}"</p>
              <button
                onClick={() => setSearchQuery('')}
                className="text-primary-600 hover:text-primary-700 font-medium mt-2"
              >
                Clear search
              </button>
            </div>
          ) : (
            <div className="divide-y">
              {filteredFaqs.map((category) => (
                <div key={category.category} className="p-6">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    {category.category}
                  </h3>
                  <div className="space-y-3">
                    {category.questions.map((faq) => (
                      <div key={faq.id} className="border rounded-lg">
                        <button
                          onClick={() => toggleFaq(faq.id)}
                          className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
                        >
                          <span className="font-medium text-gray-900">
                            {faq.question}
                          </span>
                          {expandedFaq === faq.id ? (
                            <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          )}
                        </button>
                        {expandedFaq === faq.id && (
                          <div className="px-4 pb-4">
                            <p className="text-gray-600">{faq.answer}</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Still Need Help */}
        <div className="mt-12 bg-gradient-to-r from-primary-50 to-purple-50 rounded-lg p-8 text-center border border-primary-100">
          <MessageCircle className="w-12 h-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Still need help?
          </h3>
          <p className="text-gray-600 mb-6">
            Our support team is here to help you get the most out of Drywall.ai
          </p>
          <div className="flex justify-center space-x-4">
            <a
              href="mailto:support@drywall.ai"
              className="btn btn-primary"
            >
              Email Support
            </a>
            <a
              href="/docs"
              className="btn btn-secondary"
            >
              View Documentation
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
