export default function AboutPage() {
  return (
    <div className="bg-white py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            About WizardSofts
          </h1>

          <div className="mt-8 space-y-8 text-gray-700">
            {/* Hero Statement */}
            <div className="border-l-4 border-primary pl-4">
              <p className="text-xl font-medium text-gray-900">
                We turn business complexity into software simplicity. Since 2016, we&apos;ve
                delivered 20+ ERP and POS solutions—and now we&apos;re pioneering the future of
                FinTech and AI.
              </p>
            </div>

            {/* Our Story */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Our Story</h2>
              <div className="mt-4 space-y-4">
                <p>
                  Founded in 2016, WizardSofts began with a clear mission: help businesses
                  streamline their operations through intelligent software. We started in a small
                  office with big ambitions, building custom ERP and POS systems for retail and
                  service industries that needed more than off-the-shelf solutions.
                </p>
                <p>
                  By 2018, we had expanded into cloud services and cybersecurity, recognizing that
                  our clients needed not just great software, but secure, scalable infrastructure.
                  Our expertise in building transactional systems gave us unique insights into data
                  security and system resilience.
                </p>
                <p>
                  In 2020, we were recognized as a leader in digital transformation solutions—a
                  validation of our team&apos;s ability to help businesses adapt and thrive during
                  unprecedented change. Today, we&apos;re channeling that expertise into FinTech
                  innovation and AI-powered solutions, building the next generation of financial and
                  business intelligence tools.
                </p>
              </div>
            </div>

            {/* By The Numbers */}
            <div className="rounded-lg bg-gray-50 p-6">
              <h2 className="text-2xl font-bold text-gray-900">By The Numbers</h2>
              <div className="mt-6 grid grid-cols-2 gap-6 sm:grid-cols-4">
                <div>
                  <div className="text-3xl font-bold text-primary">2016</div>
                  <div className="mt-1 text-sm text-gray-600">Founded</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary">20+</div>
                  <div className="mt-1 text-sm text-gray-600">Projects Delivered</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary">3</div>
                  <div className="mt-1 text-sm text-gray-600">Core Specializations</div>
                </div>
                <div>
                  <div className="text-3xl font-bold text-primary">9</div>
                  <div className="mt-1 text-sm text-gray-600">Years Experience</div>
                </div>
              </div>
            </div>

            {/* What Makes Us Different */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">What Makes Us Different</h2>
              <div className="mt-4 space-y-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                      ✓
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Deep Domain Expertise in ERP & POS
                    </h3>
                    <p className="mt-1 text-sm">
                      We don&apos;t just code—we understand inventory management, point-of-sale
                      workflows, and multi-location operations. Our solutions reflect real business
                      needs, not generic templates.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                      ✓
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">FinTech-Ready Architecture</h3>
                    <p className="mt-1 text-sm">
                      Our systems are built for financial transactions from day one—with audit
                      trails, compliance logging, and security that meets regulatory standards.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                      ✓
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">AI Integration Without The Hype</h3>
                    <p className="mt-1 text-sm">
                      We implement AI where it delivers measurable ROI—predictive analytics,
                      intelligent automation, and data-driven insights. No buzzwords, just results.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white">
                      ✓
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Boutique Service, Enterprise Quality
                    </h3>
                    <p className="mt-1 text-sm">
                      You work directly with senior developers and architects—no outsourcing, no
                      communication gaps. We deliver enterprise-grade solutions without enterprise
                      bureaucracy.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Our Expertise */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Our Expertise</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-gray-200 p-4">
                  <h3 className="font-semibold text-gray-900">Traditional Strengths</h3>
                  <ul className="mt-2 space-y-1 text-sm">
                    <li>• Custom ERP Systems</li>
                    <li>• Point of Sale (POS) Solutions</li>
                    <li>• Cloud Migration & Infrastructure</li>
                    <li>• Cybersecurity Implementation</li>
                  </ul>
                </div>
                <div className="rounded-lg border border-gray-200 bg-primary/5 p-4">
                  <h3 className="font-semibold text-gray-900">Current Focus</h3>
                  <ul className="mt-2 space-y-1 text-sm">
                    <li>• FinTech Platform Development</li>
                    <li>• AI-Powered Business Intelligence</li>
                    <li>• Machine Learning Integration</li>
                    <li>• Payment Systems & Compliance</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Team & Culture */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Team & Culture</h2>
              <p className="mt-4">
                Our team brings together seasoned software architects, full-stack engineers, and
                domain specialists with real-world experience in retail, finance, and enterprise
                software. We believe in continuous learning—every project is an opportunity to
                master new technologies and refine our craft.
              </p>
              <p className="mt-4">
                We work remotely, collaborate intensively, and ship incrementally. Our development
                philosophy: build it right the first time, test thoroughly, and deploy confidently.
              </p>
            </div>

            {/* CTA */}
            <div className="rounded-lg bg-primary/10 p-6 text-center">
              <h2 className="text-2xl font-bold text-gray-900">Ready to Build Something Great?</h2>
              <p className="mt-2 text-gray-700">
                Whether you need a custom ERP, a FinTech platform, or AI integration—let&apos;s talk
                about how we can help your business grow.
              </p>
              <div className="mt-6">
                <a
                  href="/contact"
                  className="inline-block rounded-md bg-primary px-6 py-3 text-white hover:bg-primary-600"
                >
                  Get In Touch
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
