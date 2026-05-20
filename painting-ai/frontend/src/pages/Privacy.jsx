export default function Privacy() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Privacy Policy
          </h1>
          <p className="text-sm text-gray-600 mb-8">
            Last Updated: May 20, 2026
          </p>

          <div className="prose prose-gray max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                1. Introduction
              </h2>
              <p className="text-gray-600 mb-4">
                Painting.ai ("we," "our," or "us") is committed to protecting your privacy. This
                Privacy Policy explains how we collect, use, disclose, and safeguard your information
                when you use our Service.
              </p>
              <p className="text-gray-600 mb-4">
                By using Painting.ai, you agree to the collection and use of information in accordance
                with this policy.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                2. Information We Collect
              </h2>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                2.1 Information You Provide
              </h3>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Account Information:</strong> Name, email address, password</li>
                <li><strong>Organization Information:</strong> Company name, team member details</li>
                <li><strong>Payment Information:</strong> Billing address, payment method (processed securely by Stripe)</li>
                <li><strong>Project Data:</strong> Floor plans, project details, room measurements, cost estimates</li>
                <li><strong>Communications:</strong> Support requests, feedback, survey responses</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                2.2 Automatically Collected Information
              </h3>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Usage Data:</strong> Pages visited, features used, time spent</li>
                <li><strong>Device Information:</strong> IP address, browser type, operating system</li>
                <li><strong>Cookies:</strong> Session cookies, authentication tokens</li>
                <li><strong>API Usage:</strong> API calls, endpoints accessed, timestamps</li>
                <li><strong>Performance Data:</strong> Processing times, error logs</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                3. How We Use Your Information
              </h2>
              <p className="text-gray-600 mb-4">
                We use your information for the following purposes:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Provide the Service:</strong> Process floor plans, generate estimates, create exports</li>
                <li><strong>Account Management:</strong> Create and maintain your account, authenticate users</li>
                <li><strong>Billing:</strong> Process payments, send invoices, manage subscriptions</li>
                <li><strong>Communication:</strong> Send transactional emails, notifications, support responses</li>
                <li><strong>Improvement:</strong> Analyze usage patterns, improve AI accuracy, develop new features</li>
                <li><strong>Security:</strong> Detect fraud, prevent abuse, enforce our Terms of Service</li>
                <li><strong>Legal Compliance:</strong> Respond to legal requests, protect our rights</li>
                <li><strong>Marketing:</strong> Send product updates, tips (with your consent, opt-out anytime)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                4. AI Processing and Data Usage
              </h2>
              <p className="text-gray-600 mb-4">
                <strong>Important:</strong> We use third-party AI services (Anthropic Claude) to process
                your floor plans and generate estimates.
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>Your floor plans are sent to Anthropic's API for AI processing</li>
                <li>Anthropic does not train on your data (per their commercial terms)</li>
                <li>Processed images are not retained by Anthropic beyond the request</li>
                <li>We may use aggregated, anonymized data to improve our AI prompts</li>
                <li>Individual project data is never shared without your consent</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                5. How We Share Your Information
              </h2>
              <p className="text-gray-600 mb-4">
                We do not sell your personal information. We share information only in these cases:
              </p>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                5.1 Service Providers
              </h3>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Anthropic:</strong> AI processing (Claude API)</li>
                <li><strong>Stripe:</strong> Payment processing</li>
                <li><strong>SendGrid:</strong> Transactional emails</li>
                <li><strong>Cloud Hosting:</strong> AWS/Railway for infrastructure</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                5.2 Legal Requirements
              </h3>
              <p className="text-gray-600 mb-4">
                We may disclose information if required by law, court order, or government request.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                5.3 Business Transfers
              </h3>
              <p className="text-gray-600 mb-4">
                If we merge, are acquired, or sell assets, your information may be transferred to
                the new entity.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 mb-3 mt-4">
                5.4 With Your Consent
              </h3>
              <p className="text-gray-600 mb-4">
                We may share information with your explicit permission (e.g., team collaboration features).
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                6. Data Security
              </h2>
              <p className="text-gray-600 mb-4">
                We implement industry-standard security measures to protect your data:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Encryption:</strong> HTTPS/TLS for data in transit, encryption at rest</li>
                <li><strong>Authentication:</strong> JWT tokens, bcrypt password hashing</li>
                <li><strong>Access Control:</strong> Role-based permissions, API key authentication</li>
                <li><strong>Monitoring:</strong> Automated security scanning, error tracking</li>
                <li><strong>Backups:</strong> Regular database backups with encrypted storage</li>
              </ul>
              <p className="text-gray-600 mb-4">
                <strong>Note:</strong> No method of transmission over the internet is 100% secure.
                We cannot guarantee absolute security.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                7. Data Retention
              </h2>
              <p className="text-gray-600 mb-4">
                We retain your information as long as your account is active or as needed to provide
                the Service:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Account Data:</strong> Retained until account deletion</li>
                <li><strong>Project Data:</strong> Retained until project deletion or account closure</li>
                <li><strong>Usage Logs:</strong> Retained for 90 days (analytics, debugging)</li>
                <li><strong>Financial Records:</strong> Retained for 7 years (legal compliance)</li>
                <li><strong>Deleted Accounts:</strong> Data permanently deleted within 30 days</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                8. Your Privacy Rights
              </h2>
              <p className="text-gray-600 mb-4">
                Depending on your location, you may have the following rights:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Access:</strong> Request a copy of your personal data</li>
                <li><strong>Correction:</strong> Update inaccurate information</li>
                <li><strong>Deletion:</strong> Request deletion of your data</li>
                <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
                <li><strong>Opt-Out:</strong> Unsubscribe from marketing emails</li>
                <li><strong>Object:</strong> Object to certain data processing</li>
              </ul>
              <p className="text-gray-600 mb-4">
                To exercise these rights, contact us at{' '}
                <a href="mailto:privacy@painting.ai" className="text-primary-600 hover:text-primary-700 font-medium">
                  privacy@painting.ai
                </a>
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                9. International Data Transfers
              </h2>
              <p className="text-gray-600 mb-4">
                Your information may be transferred to and processed in the United States or other
                countries where our service providers operate. By using the Service, you consent to
                such transfers.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                10. Children's Privacy
              </h2>
              <p className="text-gray-600 mb-4">
                Our Service is not intended for users under 18. We do not knowingly collect information
                from children. If you believe we have collected data from a child, please contact us
                immediately.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                11. Cookies and Tracking
              </h2>
              <p className="text-gray-600 mb-4">
                We use cookies and similar technologies:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Essential Cookies:</strong> Required for authentication, security</li>
                <li><strong>Analytics Cookies:</strong> Understand how you use the Service</li>
                <li><strong>Preference Cookies:</strong> Remember your settings</li>
              </ul>
              <p className="text-gray-600 mb-4">
                You can disable cookies in your browser settings, but this may limit functionality.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                12. Third-Party Links
              </h2>
              <p className="text-gray-600 mb-4">
                Our Service may contain links to third-party websites. We are not responsible for
                their privacy practices. Please review their privacy policies.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                13. California Privacy Rights (CCPA)
              </h2>
              <p className="text-gray-600 mb-4">
                California residents have additional rights under the CCPA:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>Right to know what personal information is collected</li>
                <li>Right to know if personal information is sold or disclosed</li>
                <li>Right to opt-out of the sale of personal information (we do not sell)</li>
                <li>Right to deletion</li>
                <li>Right to non-discrimination for exercising CCPA rights</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                14. GDPR Compliance (EU Users)
              </h2>
              <p className="text-gray-600 mb-4">
                For users in the European Economic Area:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>We process data based on consent, contract performance, or legitimate interests</li>
                <li>You have the right to lodge a complaint with a supervisory authority</li>
                <li>Data transfers comply with GDPR requirements</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                15. Changes to This Policy
              </h2>
              <p className="text-gray-600 mb-4">
                We may update this Privacy Policy from time to time. We will notify you of material
                changes via email or in-app notification. The "Last Updated" date at the top reflects
                the latest revision.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                16. Contact Us
              </h2>
              <p className="text-gray-600 mb-4">
                For privacy-related questions or requests:
              </p>
              <p className="text-gray-600">
                Email: <a href="mailto:privacy@painting.ai" className="text-primary-600 hover:text-primary-700 font-medium">privacy@painting.ai</a><br />
                Mail: Painting.ai Inc., 123 Innovation Drive, San Francisco, CA 94102<br />
                Data Protection Officer: <a href="mailto:dpo@painting.ai" className="text-primary-600 hover:text-primary-700 font-medium">dpo@painting.ai</a>
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
