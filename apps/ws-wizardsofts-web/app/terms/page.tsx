export default function TermsPage() {
  return (
    <div className="bg-white py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Terms of Service
          </h1>

          <div className="mt-8 space-y-6 text-gray-700">
            <p className="text-sm text-gray-500">Last updated: {new Date().toLocaleDateString()}</p>

            <h2 className="text-2xl font-bold text-gray-900">1. Acceptance of Terms</h2>
            <p>
              By accessing and using WizardSofts&apos; website and services, you accept and agree to
              be bound by the terms and provision of this agreement. If you do not agree to these
              terms, please do not use our services.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">2. Use of Services</h2>
            <p>
              Our services are provided &quot;as is&quot; for your use, subject to these Terms of
              Service. You agree to use our services only for lawful purposes and in accordance with
              these terms.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">3. Intellectual Property</h2>
            <p>
              All content, features, and functionality on this website are owned by WizardSofts and
              are protected by international copyright, trademark, and other intellectual property
              laws.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">4. Service Availability</h2>
            <p>
              We strive to provide reliable services but do not guarantee that our services will be
              uninterrupted, timely, secure, or error-free. We reserve the right to modify or
              discontinue services at any time without notice.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">5. Limitation of Liability</h2>
            <p>
              WizardSofts shall not be liable for any indirect, incidental, special, consequential,
              or punitive damages resulting from your use or inability to use our services.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">6. Changes to Terms</h2>
            <p>
              We reserve the right to modify these terms at any time. Changes will be effective
              immediately upon posting to this page. Your continued use of our services constitutes
              acceptance of any changes.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">7. Governing Law</h2>
            <p>
              These terms shall be governed by and construed in accordance with applicable laws,
              without regard to conflict of law principles.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">8. Contact Information</h2>
            <p>
              If you have any questions about these Terms of Service, please contact us through our
              contact form.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
