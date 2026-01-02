import { notFound } from "next/navigation";
import Link from "next/link";
import { services } from "@/lib/services";

export async function generateStaticParams() {
  return services.map((service) => ({
    slug: service.slug,
  }));
}

export default async function ServiceDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const service = services.find((s) => s.slug === slug);

  if (!service) {
    notFound();
  }

  return (
    <div className="bg-white py-12">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/services"
          className="inline-flex items-center text-sm font-medium text-primary hover:underline"
        >
          ← Back to Services
        </Link>

        {/* Hero Section */}
        <div className="mt-8">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            {service.title}
          </h1>
          <p className="mt-4 text-xl text-gray-600">{service.shortDescription}</p>

          {service.longDescription && (
            <div className="prose prose-lg mt-6 text-gray-700">
              <p>{service.longDescription}</p>
            </div>
          )}
        </div>

        {/* Quick Info */}
        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {service.pricing && (
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm font-medium text-gray-500">Investment</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{service.pricing}</div>
            </div>
          )}
          {service.timeline && (
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm font-medium text-gray-500">Timeline</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{service.timeline}</div>
            </div>
          )}
          {service.industries && service.industries.length > 0 && (
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-sm font-medium text-gray-500">Industries</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">
                {service.industries.slice(0, 2).join(", ")}
                {service.industries.length > 2 && ` +${service.industries.length - 2}`}
              </div>
            </div>
          )}
        </div>

        {/* Key Features */}
        {service.features && service.features.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900">What You Get</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {service.features.map((feature, index) => (
                <div key={index} className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-sm text-white">
                      ✓
                    </div>
                  </div>
                  <div className="text-gray-700">{feature}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Benefits */}
        {service.benefits && service.benefits.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900">Business Impact</h2>
            <div className="mt-6 space-y-4">
              {service.benefits.map((benefit, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 rounded-lg border-l-4 border-primary bg-primary/5 p-4"
                >
                  <div className="text-2xl">📈</div>
                  <div className="font-medium text-gray-900">{benefit}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Case Study */}
        {service.caseStudy && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900">Real Results</h2>
            <div className="mt-6 rounded-lg border-2 border-primary/20 bg-primary/5 p-6">
              <div className="flex items-start gap-4">
                <div className="text-4xl">💡</div>
                <div>
                  <p className="text-gray-700">{service.caseStudy}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Industries Served */}
        {service.industries && service.industries.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900">Industries We Serve</h2>
            <div className="mt-6 flex flex-wrap gap-3">
              {service.industries.map((industry) => (
                <span
                  key={industry}
                  className="rounded-full border border-primary bg-white px-4 py-2 text-sm font-medium text-gray-900"
                >
                  {industry}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* CTA Section */}
        <div className="mt-12 rounded-lg bg-gray-900 p-8 text-center text-white">
          <h2 className="text-2xl font-bold">Ready to Get Started?</h2>
          <p className="mt-2 text-gray-300">
            Schedule a free 30-minute consultation to discuss your project and see if we&apos;re the
            right fit.
          </p>
          <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/contact"
              className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-base font-medium text-white hover:bg-primary-600"
            >
              Schedule Consultation
            </Link>
            <Link
              href="/services"
              className="inline-flex items-center justify-center rounded-md border border-white px-6 py-3 text-base font-medium text-white hover:bg-white hover:text-gray-900"
            >
              View All Services
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
