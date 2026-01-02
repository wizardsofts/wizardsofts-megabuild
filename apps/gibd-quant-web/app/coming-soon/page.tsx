import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Coming Soon | Guardian Investment BD",
  description:
    "Guardian Investment BD - AI-Powered Trading Signals for Dhaka Stock Exchange. Coming Soon.",
};

/**
 * Coming Soon Page
 *
 * Displayed when the app is accessed via guardianinvestmentbd.com domain
 * while the app is still under development.
 */
export default function ComingSoonPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center px-4">
      <div className="text-center max-w-2xl mx-auto">
        {/* Logo / Brand */}
        <div className="mb-8">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-2">
            Guardian Investment BD
          </h1>
          <div className="h-1 w-32 bg-gradient-to-r from-blue-400 to-emerald-400 mx-auto rounded-full" />
        </div>

        {/* Coming Soon Message */}
        <div className="mb-12">
          <h2 className="text-2xl md:text-3xl font-semibold text-blue-200 mb-4">
            Coming Soon
          </h2>
          <p className="text-lg text-gray-300 leading-relaxed">
            We&apos;re building something amazing. Our AI-powered trading signal
            platform for Dhaka Stock Exchange is under development.
          </p>
        </div>

        {/* Features Preview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <div className="text-3xl mb-3">📊</div>
            <h3 className="text-white font-semibold mb-2">Trading Signals</h3>
            <p className="text-gray-400 text-sm">
              Real-time BUY, SELL, and HOLD signals
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <div className="text-3xl mb-3">🤖</div>
            <h3 className="text-white font-semibold mb-2">AI-Powered</h3>
            <p className="text-gray-400 text-sm">
              Advanced quantitative analysis
            </p>
          </div>
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/10">
            <div className="text-3xl mb-3">📈</div>
            <h3 className="text-white font-semibold mb-2">DSE Focused</h3>
            <p className="text-gray-400 text-sm">
              Dhaka Stock Exchange coverage
            </p>
          </div>
        </div>

        {/* Contact Section */}
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-8 border border-white/10">
          <p className="text-gray-300 mb-4">
            For inquiries, please contact us at:
          </p>
          <a
            href="mailto:info@guardianinvestmentbd.com"
            className="inline-flex items-center gap-2 text-xl font-semibold text-blue-400 hover:text-blue-300 transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            info@guardianinvestmentbd.com
          </a>
        </div>

        {/* Footer */}
        <p className="mt-12 text-gray-500 text-sm">
          &copy; {new Date().getFullYear()} Guardian Investment BD. All rights
          reserved.
        </p>
      </div>
    </div>
  );
}
