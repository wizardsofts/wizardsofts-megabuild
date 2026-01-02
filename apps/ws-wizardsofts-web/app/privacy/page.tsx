export default function PrivacyPage() {
  return (
    <div className="bg-white py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Privacy Policy
          </h1>

          <div className="mt-8 space-y-6 text-gray-700">
            <p className="text-sm text-gray-500">Last updated: {new Date().toLocaleDateString()}</p>

            <h2 className="text-2xl font-bold text-gray-900">1. Information We Collect</h2>
            <p>
              When you use our contact form or interact with our services, we may collect personal
              information such as your name, email address, phone number, company name, and message
              content. We collect this information to respond to your inquiries and provide our
              services.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">2. How We Use Your Information</h2>
            <p>We use the information we collect to:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Respond to your inquiries and provide customer support</li>
              <li>Send you information about our services</li>
              <li>Improve our website and services</li>
              <li>Comply with legal obligations</li>
              <li>Prevent fraud and enhance security</li>
            </ul>

            <h2 className="text-2xl font-bold text-gray-900">3. Data Retention</h2>
            <p>
              We retain contact form submissions for 30 days, after which they are automatically
              purged from our system. Other data may be retained for longer periods as required by
              law or legitimate business purposes.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">4. Data Security</h2>
            <p>
              We implement appropriate technical and organizational measures to protect your
              personal information against unauthorized access, alteration, disclosure, or
              destruction. However, no method of transmission over the Internet is 100% secure.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">5. Sharing Your Information</h2>
            <p>
              We do not sell, trade, or rent your personal information to third parties. We may
              share information with trusted service providers who assist in operating our website,
              conducting business, or serving our users, as long as those parties agree to keep this
              information confidential.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">6. Cookies and Tracking</h2>
            <p>
              Our website may use cookies and similar tracking technologies to enhance user
              experience. You can control cookie preferences through your browser settings.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">7. Your Rights</h2>
            <p>You have the right to:</p>
            <ul className="list-disc space-y-2 pl-6">
              <li>Access the personal information we hold about you</li>
              <li>Request correction of inaccurate information</li>
              <li>Request deletion of your information</li>
              <li>Opt-out of marketing communications</li>
              <li>Lodge a complaint with a supervisory authority</li>
            </ul>

            <h2 className="text-2xl font-bold text-gray-900">8. Third-Party Links</h2>
            <p>
              Our website may contain links to third-party websites. We are not responsible for the
              privacy practices of these external sites. We encourage you to review their privacy
              policies.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">9. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. Changes will be posted on this
              page with an updated revision date. Your continued use of our services after changes
              constitutes acceptance of the updated policy.
            </p>

            <h2 className="text-2xl font-bold text-gray-900">10. Contact Us</h2>
            <p>
              If you have questions or concerns about this Privacy Policy or how we handle your
              personal information, please contact us through our contact form.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
