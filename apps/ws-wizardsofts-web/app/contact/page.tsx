import ContactForm from "@/components/ContactForm";

export default function ContactPage() {
  return (
    <div className="bg-gray-50 py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl">
          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Get in Touch
            </h1>
            <p className="mt-4 text-lg text-gray-600">
              Have a question or want to work together? We&apos;d love to hear from you.
            </p>
          </div>

          <div className="mt-12 bg-white px-6 py-8 shadow sm:rounded-lg sm:px-10">
            <ContactForm />
          </div>

          <div className="mt-8 text-center text-sm text-gray-500">
            <p>We typically respond within 24-48 hours during business days.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
