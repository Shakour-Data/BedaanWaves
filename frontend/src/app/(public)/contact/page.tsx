import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact Us | BedaanWaves",
  description: "Get in touch with the BedaanWaves team. We are here to help with any questions about our platform, pricing, or enterprise solutions.",
};

const contactMethods = [
  {
    icon: "📧",
    title: "Email",
    value: "support@bedaanwaves.com",
    description: "We typically respond within 24 hours.",
  },
  {
    icon: "💬",
    title: "Live Chat",
    value: "Available 24/7",
    description: "Instant support for Pro and Enterprise users.",
  },
  {
    icon: "📞",
    title: "Phone",
    value: "+1 (555) 123-4567",
    description: "Mon-Fri, 9am-6pm EST.",
  },
];

const offices = [
  {
    city: "New York",
    address: "123 Wall Street, Suite 400\nNew York, NY 10005",
  },
  {
    city: "London",
    address: "45 Canary Wharf\nLondon, E14 5AB, UK",
  },
  {
    city: "Singapore",
    address: "88 Marina Bay\nSingapore 018956",
  },
];

export default function ContactPage() {
  return (
    <div className="page-transition-enter">
      {/* Hero */}
      <section className="relative overflow-hidden py-16 lg:py-24">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
        </div>
        <div className="relative container-grid">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl">
              Contact <span className="text-[var(--color-primary)]">Us</span>
            </h1>
            <p className="mt-6 text-lg text-[var(--color-text-secondary)]">
              Have a question or need support? Our team is here to help. Reach out through any of the channels below and we will get back to you as soon as possible.
            </p>
          </div>
        </div>
      </section>

      {/* Contact Methods */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="grid gap-8 md:grid-cols-3">
            {contactMethods.map((method, index) => (
              <div
                key={index}
                className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg text-center"
              >
                <div className="text-4xl mb-4">{method.icon}</div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {method.title}
                </h3>
                <p className="mt-2 text-sm font-medium text-[var(--color-primary)]">
                  {method.value}
                </p>
                <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                  {method.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="grid gap-12 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl font-bold text-[var(--color-text-primary)]">
                Send Us a Message
              </h2>
              <p className="mt-4 text-[var(--color-text-secondary)]">
                Fill out the form and our team will get back to you within 24 hours. For urgent matters, please use our live chat or phone support.
              </p>
              <div className="mt-8 space-y-6">
                {offices.map((office, index) => (
                  <div key={index} className="flex gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                      📍
                    </div>
                    <div>
                      <h4 className="font-semibold text-[var(--color-text-primary)]">
                        {office.city}
                      </h4>
                      <p className="text-sm text-[var(--color-text-secondary)] whitespace-pre-line">
                        {office.address}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <form className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-sm">
              <div className="space-y-6">
                <div className="grid gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                      First Name
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                      Last Name
                    </label>
                    <input
                      type="text"
                      className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                      placeholder="Doe"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                    placeholder="john@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                    Subject
                  </label>
                  <select className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]">
                    <option>General Inquiry</option>
                    <option>Technical Support</option>
                    <option>Billing</option>
                    <option>Enterprise Sales</option>
                    <option>Partnership</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                    Message
                  </label>
                  <textarea
                    rows={5}
                    className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                    placeholder="How can we help you?"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full rounded-lg bg-[var(--color-primary)] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-primary-hover)]"
                >
                  Send Message
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <h2 className="text-3xl font-bold text-[var(--color-text-primary)] mb-12 text-center">
            Frequently Asked Questions
          </h2>
          <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
            {[
              {
                q: "How do I get started with BedaanWaves?",
                a: "Simply create a free account and start exploring our platform. No credit card required for the Starter plan.",
              },
              {
                q: "Is my data secure?",
                a: "Yes, we use bank-level encryption and security protocols to protect your data. We never share your information with third parties.",
              },
              {
                q: "Can I cancel my subscription anytime?",
                a: "Yes, you can cancel your subscription at any time. Your access will continue until the end of your billing period.",
              },
              {
                q: "Do you offer API access?",
                a: "Yes, API access is available on our Enterprise plan. Contact our sales team for more information.",
              },
            ].map((faq, index) => (
              <div
                key={index}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6"
              >
                <h3 className="font-semibold text-[var(--color-text-primary)]">
                  {faq.q}
                </h3>
                <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                  {faq.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
