import Link from "next/link";

export default function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary to-primary-600 py-20 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
              ERP, POS & FinTech Solutions
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-xl">
              Built by specialists who understand transactional systems, financial integrity, and
              business operations. Since 2016.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Link
                href="/services"
                className="rounded-md bg-white px-6 py-3 text-base font-medium text-primary hover:bg-gray-100"
              >
                View Our Services
              </Link>
              <Link
                href="/contact"
                className="rounded-md border-2 border-white px-6 py-3 text-base font-medium text-white hover:bg-white hover:text-primary"
              >
                Schedule Consultation
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-b border-gray-200 bg-white py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 text-center sm:grid-cols-4">
            <div>
              <div className="text-3xl font-bold text-primary">2016</div>
              <div className="mt-1 text-sm text-gray-600">Founded</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">20+</div>
              <div className="mt-1 text-sm text-gray-600">Projects Delivered</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">6</div>
              <div className="mt-1 text-sm text-gray-600">Core Services</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-primary">9</div>
              <div className="mt-1 text-sm text-gray-600">Years Experience</div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Specializations */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">Our Core Specializations</h2>
            <p className="mt-4 text-lg text-gray-600">
              We don&apos;t do everything—we excel at ERP, POS, and FinTech
            </p>
          </div>

          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-6 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Custom ERP Solutions</h3>
              <p className="mt-2 text-sm text-gray-600">
                Integrate inventory, purchasing, sales, and accounting into one system. Replace
                spreadsheets with real-time business intelligence.
              </p>
              <p className="mt-3 text-sm font-semibold text-primary">Starting at $25,000</p>
            </div>

            <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-6 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">POS Systems</h3>
              <p className="mt-2 text-sm text-gray-600">
                Lightning-fast checkout that works offline. Integrated payment processing, inventory
                sync, and customer loyalty programs.
              </p>
              <p className="mt-3 text-sm font-semibold text-primary">Starting at $15,000</p>
            </div>

            <div className="rounded-lg border-2 border-primary/20 bg-primary/5 p-6 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">FinTech Platforms</h3>
              <p className="mt-2 text-sm text-gray-600">
                Payment systems, compliance-ready architecture, and audit trails built by engineers
                who understand financial integrity.
              </p>
              <p className="mt-3 text-sm font-semibold text-primary">Starting at $50,000</p>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Link href="/services" className="text-primary hover:underline">
              View all services →
            </Link>
          </div>
        </div>
      </section>

      {/* Why Choose Us Section */}
      <section className="bg-gray-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">Why Choose WizardSofts?</h2>
            <p className="mt-4 text-lg text-gray-600">
              Not just another dev shop—we&apos;re domain specialists
            </p>
          </div>

          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Deep Domain Expertise</h3>
              <p className="mt-2 text-sm text-gray-600">
                We understand inventory workflows, financial transactions, and compliance—not just
                code
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Proven Track Record</h3>
              <p className="mt-2 text-sm text-gray-600">
                20+ systems deployed since 2016. We know the pitfalls and how to avoid them
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary text-white">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                Boutique Service, Enterprise Quality
              </h3>
              <p className="mt-2 text-sm text-gray-600">
                Work directly with senior engineers. No outsourcing, no communication gaps
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-900 py-16 text-white">
        <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold">Ready to Build Something Great?</h2>
          <p className="mt-4 text-lg text-gray-300">
            Schedule a free 30-minute consultation to discuss your ERP, POS, or FinTech project
          </p>
          <div className="mt-8">
            <Link
              href="/contact"
              className="inline-flex items-center rounded-md bg-primary px-6 py-3 text-base font-medium text-white hover:bg-primary-600"
            >
              Schedule Consultation
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
