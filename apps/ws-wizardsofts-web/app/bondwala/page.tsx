"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function BondWalaPage() {
  const [openFaqs, setOpenFaqs] = useState<number[]>([]);
  const [launchDate, setLaunchDate] = useState<string>("");

  useEffect(() => {
    // Calculate 7 days from now
    const now = new Date();
    const launch = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    // Format as "Month Day, Year" (e.g., "January 5, 2026")
    const formatted = launch.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    setLaunchDate(formatted);
  }, []);

  const toggleFaq = (index: number) => {
    setOpenFaqs((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const faqs = [
    {
      question: "Is BondWala official?",
      answer:
        "No. BondWala is an unofficial tracker app developed by Wizard of Softs. It uses publicly available Bangladesh Bank Prize Bond draw data. Always verify prizes through official Bangladesh Bank channels.",
    },
    {
      question: "Do I need a login?",
      answer:
        "No. BondWala is completely anonymous. No login, no account, no personal data collected.",
    },
    {
      question: "Where is my data stored?",
      answer:
        "Your bonds are stored locally on your phone only. We never store your bond information on our servers.",
    },
    {
      question: "Is it safe to use?",
      answer:
        "Yes. Your bond data is encrypted on your device. We don't collect personal information and don't sync data to the cloud.",
    },
    {
      question: "How does OCR scanning work?",
      answer:
        "Point your camera at a bond serial number. The app uses AI to instantly detect and read the 7-digit serial number. You can manually correct if needed.",
    },
    {
      question: "Will I definitely be notified of wins?",
      answer:
        "Yes, if you have notifications enabled. However, verify through official Bangladesh Bank channels before claiming.",
    },
    {
      question: "Can I use this on multiple phones?",
      answer:
        "Your bonds are stored locally, so you'd need to add them separately on each phone. You can manually copy serial numbers or take screenshots.",
    },
    {
      question: "How often are draw results updated?",
      answer:
        "BondWala fetches the latest 8 draws from Bangladesh Bank. Updates are automatic when draws are published (typically 4 per year).",
    },
    {
      question: "Is this app affiliated with Bangladesh Bank?",
      answer:
        "No. This is an independent tracker app. Bangladesh Bank information is public data that we access to help you track bonds.",
    },
    {
      question: "What should I do if I win?",
      answer:
        "BondWala will notify you and show the prize amount. To claim: 1. Visit Bangladesh Bank official website, 2. Download claim form, 3. Submit with bond and documents, 4. Follow official procedures.",
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-primary via-primary to-primary-600 py-20 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              Track Easy, Win Sure
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-white/90">
              Bangladesh Prize Bond tracker app that helps you easily track your bonds and get
              instant notifications when you win. No login required, no cloud syncing needed—your
              bonds stay private on your device.
            </p>
            <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:justify-center">
              <div className="inline-block rounded-md bg-white px-8 py-3 font-semibold text-primary">
                Coming Soon - {launchDate || "January 2026"}
              </div>
              <a
                href="#how-it-works"
                className="inline-block rounded-md border-2 border-white px-8 py-3 font-semibold text-white hover:bg-white/10 transition-colors"
              >
                Learn More
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Everything you need to track your bonds and never miss a win
            </p>
          </div>

          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">📷</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">OCR Bond Scanning</h3>
              <p className="mt-2 text-gray-600">
                Point your camera at a bond, and BondWala instantly detects the serial number. No
                typing, no mistakes. The app uses advanced ML technology to read bond numbers in
                seconds.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ Save time and accuracy</p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">🏆</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">Automatic Win Detection</h3>
              <p className="mt-2 text-gray-600">
                BondWala automatically checks your bonds against the latest 8 prize draws from
                Bangladesh Bank. When you win, the app highlights it immediately with a winning
                badge.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ Never miss a win</p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">🔔</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">Instant Notifications</h3>
              <p className="mt-2 text-gray-600">
                Get push notifications the moment your bonds appear in a draw. Configure
                notification preferences in settings to receive alerts exactly when you want them.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ Know about wins immediately</p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">🔒</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">Private & Secure</h3>
              <p className="mt-2 text-gray-600">
                Your bond data stays on your device. BondWala doesn&apos;t require a login or sync to
                cloud servers. Your privacy is protected with local encryption.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ Complete privacy control</p>
            </div>

            {/* Feature 5 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">✨</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">Simple & Intuitive</h3>
              <p className="mt-2 text-gray-600">
                Designed for everyone. Clean, easy-to-understand interface. Add bonds with a tap,
                search instantly, and view your wins at a glance.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ No learning curve</p>
            </div>

            {/* Feature 6 */}
            <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="text-4xl">📅</div>
              <h3 className="mt-4 text-xl font-semibold text-gray-900">Draw Information</h3>
              <p className="mt-2 text-gray-600">
                View complete prize draw results for the last 8 draws (approximately 2 years). See
                prize breakdowns for each tier and when the next draws are happening.
              </p>
              <p className="mt-3 text-sm font-medium text-primary">✓ Stay informed</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="bg-gray-50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              How It Works
            </h2>
            <p className="mt-4 text-lg text-gray-600">Get started in 5 simple steps</p>
          </div>

          <div className="mt-16 space-y-8 md:space-y-0 md:grid md:grid-cols-5 md:gap-4">
            {[
              {
                step: "1",
                title: "Download & Install",
                description: "Choose iOS or Android, install from app store, grant permissions",
              },
              {
                step: "2",
                title: "Add Your Bonds",
                description: "Scan with camera or type serial number. Bonds saved privately on device",
              },
              {
                step: "3",
                title: "Check Latest Draws",
                description: "App automatically fetches latest prize draws. View results for last 8 draws",
              },
              {
                step: "4",
                title: "Get Notifications",
                description: "Instant push notification when your bond wins. Winning badge on card",
              },
              {
                step: "5",
                title: "Claim Prize",
                description: "Visit Bangladesh Bank website. Follow official claim procedures",
              },
            ].map((item, index) => (
              <div key={index} className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white font-bold">
                    {item.step}
                  </div>
                  <h3 className="mt-4 font-semibold text-gray-900">{item.title}</h3>
                  <p className="mt-2 text-sm text-gray-600">{item.description}</p>
                </div>
                {index < 4 && (
                  <div className="hidden md:block absolute top-6 left-1/2 w-4/12 h-0.5 bg-gradient-to-r from-primary to-transparent"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="bg-gray-50 py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div
                key={index}
                className="rounded-lg border border-gray-200 overflow-hidden transition-all"
              >
                <button
                  onClick={() => toggleFaq(index)}
                  className="w-full px-6 py-4 text-left font-medium text-gray-900 hover:bg-gray-50 flex justify-between items-center"
                  aria-expanded={openFaqs.includes(index)}
                >
                  {faq.question}
                  <span className="text-primary">{openFaqs.includes(index) ? "−" : "+"}</span>
                </button>
                {openFaqs.includes(index) && (
                  <div className="border-t border-gray-200 px-6 py-4 bg-white text-gray-700">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Coming Soon Section */}
      <section id="download" className="py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Coming Soon
          </h2>
          <p className="mt-4 text-lg text-gray-600">
            BondWala will be available on iOS and Android starting {launchDate || "soon"}.
          </p>

          <div className="mt-8 inline-block rounded-lg bg-gradient-to-r from-primary/10 to-primary/5 px-12 py-8 border-2 border-primary/20">
            <div className="text-sm font-medium text-gray-600 uppercase tracking-wide">Expected Launch Date</div>
            <div className="mt-2 text-4xl font-bold text-primary">{launchDate || "Coming Soon"}</div>
            <div className="mt-4 text-gray-600">Stay tuned for updates!</div>
          </div>

          {/* Download links hidden until release */}
          {/*
          <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <a
              href="https://play.google.com/store"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block rounded-md bg-primary px-8 py-4 font-semibold text-white hover:bg-primary-600 transition-colors"
            >
              <div className="text-sm text-white/80">Get it on</div>
              <div>Google Play</div>
            </a>
            <a
              href="https://apps.apple.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block rounded-md bg-gray-900 px-8 py-4 font-semibold text-white hover:bg-gray-800 transition-colors"
            >
              <div className="text-sm text-white/80">Download on</div>
              <div>App Store</div>
            </a>
          </div>
          */}

        </div>
      </section>

      {/* Support & Contact Section */}
      <section id="support" className="bg-gradient-to-r from-primary/10 to-primary/5 py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl mb-4">
              Need Help?
            </h2>
            <p className="text-lg text-gray-600">
              Email us at <span className="font-semibold text-primary">bondwala@wizardsofts.com</span>
            </p>
            <p className="text-sm text-gray-500 mt-2">Response time: 24-48 hours</p>
          </div>
        </div>
      </section>


    </div>
  );
}
