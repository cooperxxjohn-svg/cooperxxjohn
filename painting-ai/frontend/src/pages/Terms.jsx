export default function Terms() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Terms of Service
          </h1>
          <p className="text-sm text-gray-600 mb-8">
            Last Updated: May 20, 2026
          </p>

          <div className="prose prose-gray max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                1. Acceptance of Terms
              </h2>
              <p className="text-gray-600 mb-4">
                By accessing and using Drywall.ai ("Service"), you accept and agree to be bound by
                the terms and provision of this agreement. If you do not agree to these terms,
                please do not use our Service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                2. Description of Service
              </h2>
              <p className="text-gray-600 mb-4">
                Drywall.ai is a SaaS platform that provides AI-powered painting estimation services
                for contractors. The Service includes:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>AI-powered floor plan analysis and room detection</li>
                <li>Automated painting cost estimation</li>
                <li>Assembly breakdown and detailed line item generation</li>
                <li>Excel and PDF export generation</li>
                <li>Public API access (on applicable plans)</li>
                <li>Team collaboration features (on applicable plans)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                3. User Accounts
              </h2>
              <p className="text-gray-600 mb-4">
                You must create an account to use the Service. You are responsible for:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>Maintaining the confidentiality of your account credentials</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized use</li>
                <li>Ensuring your account information is accurate and up-to-date</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                4. Subscription Plans and Billing
              </h2>
              <p className="text-gray-600 mb-4">
                <strong>Free Trial:</strong> New users receive a 14-day free trial with full access
                to all features. No credit card required to start the trial.
              </p>
              <p className="text-gray-600 mb-4">
                <strong>Paid Plans:</strong> After the trial period, you must subscribe to a paid
                plan to continue using the Service. Plans are billed monthly in advance.
              </p>
              <p className="text-gray-600 mb-4">
                <strong>Payment:</strong> By subscribing, you authorize us to charge your payment
                method on a recurring basis. All fees are non-refundable except as required by law.
              </p>
              <p className="text-gray-600 mb-4">
                <strong>Cancellation:</strong> You may cancel your subscription at any time. Upon
                cancellation, you will retain access until the end of your current billing period.
              </p>
              <p className="text-gray-600 mb-4">
                <strong>Plan Changes:</strong> You may upgrade or downgrade your plan at any time.
                Changes take effect immediately and are prorated.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                5. Usage Limits and Restrictions
              </h2>
              <p className="text-gray-600 mb-4">
                Usage limits apply based on your subscription plan:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li><strong>Starter:</strong> 50 projects per month, 1 user</li>
                <li><strong>Pro:</strong> Unlimited projects, API access, up to 5 team members</li>
                <li><strong>Enterprise:</strong> Custom limits based on agreement</li>
              </ul>
              <p className="text-gray-600 mb-4">
                You may not:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>Resell or redistribute the Service</li>
                <li>Reverse engineer or attempt to extract source code</li>
                <li>Use the Service for illegal purposes</li>
                <li>Abuse, harass, or harm others through the Service</li>
                <li>Circumvent usage limits or security measures</li>
                <li>Use automated means to access the Service beyond API rate limits</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                6. AI-Generated Estimates - Accuracy Disclaimer
              </h2>
              <p className="text-gray-600 mb-4">
                <strong>Important:</strong> Estimates generated by our AI are approximations based
                on the information provided. While we strive for accuracy:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>You should always review and verify AI-generated estimates</li>
                <li>Final pricing should be confirmed with on-site inspections</li>
                <li>We are not liable for inaccuracies in AI-generated estimates</li>
                <li>Estimates are tools to assist your workflow, not replace professional judgment</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                7. Intellectual Property
              </h2>
              <p className="text-gray-600 mb-4">
                <strong>Your Content:</strong> You retain all rights to content you upload
                (floor plans, project data). You grant us a limited license to process your
                content to provide the Service.
              </p>
              <p className="text-gray-600 mb-4">
                <strong>Our Property:</strong> The Service, including all software, algorithms,
                designs, and documentation, is owned by Drywall.ai and protected by intellectual
                property laws.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                8. Data Privacy
              </h2>
              <p className="text-gray-600 mb-4">
                We collect and process your data as described in our{' '}
                <a href="/privacy" className="text-primary-600 hover:text-primary-700 font-medium">
                  Privacy Policy
                </a>
                . By using the Service, you consent to such processing.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                9. Service Availability
              </h2>
              <p className="text-gray-600 mb-4">
                We strive to provide reliable service but do not guarantee uninterrupted access.
                We may modify, suspend, or discontinue the Service at any time with reasonable notice.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                10. Limitation of Liability
              </h2>
              <p className="text-gray-600 mb-4">
                To the maximum extent permitted by law, Drywall.ai shall not be liable for any
                indirect, incidental, special, consequential, or punitive damages, including loss
                of profits, data, or business opportunities.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                11. Warranty Disclaimer
              </h2>
              <p className="text-gray-600 mb-4">
                THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED,
                INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR
                NON-INFRINGEMENT.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                12. Indemnification
              </h2>
              <p className="text-gray-600 mb-4">
                You agree to indemnify and hold harmless Drywall.ai from any claims, damages, or
                expenses arising from your use of the Service or violation of these Terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                13. Termination
              </h2>
              <p className="text-gray-600 mb-4">
                We may terminate or suspend your access immediately, without prior notice, for:
              </p>
              <ul className="list-disc pl-6 text-gray-600 mb-4 space-y-2">
                <li>Violation of these Terms</li>
                <li>Non-payment of fees</li>
                <li>Illegal or fraudulent activity</li>
                <li>At our discretion for any reason</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                14. Changes to Terms
              </h2>
              <p className="text-gray-600 mb-4">
                We reserve the right to modify these Terms at any time. We will notify you of
                material changes via email or in-app notification. Continued use of the Service
                after changes constitutes acceptance.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                15. Governing Law
              </h2>
              <p className="text-gray-600 mb-4">
                These Terms are governed by the laws of the State of Delaware, United States,
                without regard to conflict of law provisions.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                16. Contact Information
              </h2>
              <p className="text-gray-600 mb-4">
                For questions about these Terms, please contact us:
              </p>
              <p className="text-gray-600">
                Email: <a href="mailto:legal@drywall.ai" className="text-primary-600 hover:text-primary-700 font-medium">legal@drywall.ai</a><br />
                Address: Drywall.ai Inc., 123 Innovation Drive, San Francisco, CA 94102
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
