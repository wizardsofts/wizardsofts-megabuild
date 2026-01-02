import Link from "next/link";
import { services } from "@/lib/services";

export default function ServicesPage() {
  return (
    <div className="bg-white py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Our Services
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            ERP, POS, and FinTech solutions built by specialists—not generalists
          </p>
        </div>

        {/* Service Categories */}
        <div className="mt-12">
          <h2 className="text-xl font-semibold text-gray-900">Core Specializations</h2>
          <div className="mt-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {services.slice(0, 3).map((service) => (
              <Link
                key={service.id}
                href={`/services/${service.slug}`}
                className="group block rounded-lg border-2 border-primary/20 bg-primary/5 p-6 shadow-sm transition-all hover:border-primary hover:shadow-md"
              >
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-primary">
                  {service.title}
                </h3>
                <p className="mt-3 text-sm text-gray-600">{service.shortDescription}</p>

                {service.industries && service.industries.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {service.industries.slice(0, 3).map((industry) => (
                      <span
                        key={industry}
                        className="rounded-full bg-white px-2 py-1 text-xs font-medium text-gray-700"
                      >
                        {industry}
                      </span>
                    ))}
                  </div>
                )}

                {service.pricing && (
                  <p className="mt-4 text-sm font-semibold text-primary">{service.pricing}</p>
                )}

                <p className="mt-4 text-sm font-medium text-primary">Learn more →</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Supporting Services */}
        <div className="mt-16">
          <h2 className="text-xl font-semibold text-gray-900">Supporting Services</h2>
          <div className="mt-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {services.slice(3).map((service) => (
              <Link
                key={service.id}
                href={`/services/${service.slug}`}
                className="group block rounded-lg border border-gray-200 p-6 shadow-sm transition-all hover:border-primary hover:shadow-md"
              >
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-primary">
                  {service.title}
                </h3>
                <p className="mt-3 text-sm text-gray-600">{service.shortDescription}</p>

                {service.pricing && (
                  <p className="mt-4 text-sm font-semibold text-primary">{service.pricing}</p>
                )}

                <p className="mt-4 text-sm font-medium text-primary">Learn more →</p>
              </Link>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-16 rounded-lg bg-gray-50 p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900">Not Sure Which Service You Need?</h2>
          <p className="mt-2 text-gray-600">
            Schedule a free 30-minute consultation to discuss your project and get expert
            recommendations.
          </p>
          <Link
            href="/contact"
            className="mt-6 inline-block rounded-md bg-primary px-6 py-3 text-white hover:bg-primary-600"
          >
            Schedule Consultation
          </Link>
        </div>
      </div>
    </div>
  );
}
