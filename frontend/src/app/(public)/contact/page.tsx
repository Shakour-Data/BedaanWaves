import { Metadata } from "next";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { Mail, MessageCircle, Phone, MapPin, Send } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact Us | BedaanWaves",
  description: "Get in touch with the BedaanWaves team. We are here to help with any questions about our platform, pricing, or enterprise solutions.",
};

const contactMethods = [
  {
    icon: Mail,
    title: "Email",
    value: "support@bedaanwaves.com",
    description: "We typically respond within 24 hours.",
  },
  {
    icon: MessageCircle,
    title: "Live Chat",
    value: "Available 24/7",
    description: "Instant support for Pro and Enterprise users.",
  },
  {
    icon: Phone,
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
    <PublicLayout>
      <div className="page-transition-enter">
        {/* Hero */}
        <section className="relative overflow-hidden py-20 lg:py-32">
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-1/2 -right-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
            <div className="absolute -bottom-1/2 -left-1/4 h-[400px] w-[400px] rounded-full bg-[var(--color-accent)]/5 blur-3xl" />
          </div>
          <div className="relative container-grid">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary-soft)] px-4 py-1.5 mb-6">
                <span className="text-sm font-medium text-[var(--color-primary)]">Get in Touch</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl text-balance">
                Contact <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Us</span>
              </h1>
              <p className="mt-8 text-lg text-[var(--color-text-secondary)] leading-relaxed max-w-2xl">
                Have a question or need support? Our team is here to help. Reach out through any of the channels below and we will get back to you as soon as possible.
              </p>
            </div>
          </div>
        </section>

        {/* Contact Methods */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="grid gap-8 md:grid-cols-3">
              {contactMethods.map((method, index) => {
                const Icon = method.icon;
                return (
                  <div
                    key={index}
                    className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg hover:-translate-y-1 text-center"
                  >
                    <div className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] group-hover:bg-gradient-to-br group-hover:from-[var(--color-primary)] group-hover:to-[var(--color-accent)] group-hover:text-white transition-all duration-300">
                      <Icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      {method.title}
                    </h3>
                    <p className="mt-2 text-sm font-semibold text-[var(--color-primary)]">
                      {method.value}
                    </p>
                    <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                      {method.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Contact Form */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="grid gap-12 lg:grid-cols-2">
              <div>
                <h2 className="text-3xl font-bold text-[var(--color-text-primary)] text-balance">
                  Send Us a Message
                </h2>
                <p className="mt-4 text-[var(--color-text-secondary)] leading-relaxed">
                  Fill out the form and our team will get back to you within 24 hours. For urgent matters, please use our live chat or phone support.
                </p>
                <div className="mt-8 space-y-6">
                  {offices.map((office, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)]">
                        <MapPin className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-[var(--color-text-primary)]">
                          {office.city}
                        </h4>
                        <p className="text-sm text-[var(--color-text-secondary)] whitespace-pre-line leading-relaxed">
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
                        className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
                        placeholder="John"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                        Last Name
                      </label>
                      <input
                        type="text"
                        className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
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
                      className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
                      placeholder="john@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
                      Subject
                    </label>
                    <select className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all">
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
                      className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all resize-none"
                      placeholder="How can we help you?"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:-translate-y-0.5"
                  >
                    <Send className="h-4 w-4" />
                    Send Message
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <h2 className="text-3xl font-bold text-[var(--color-text-primary)] mb-12 text-center text-balance">
              Frequently Asked <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Questions</span>
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
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-sm transition-all hover:shadow-md hover:border-[var(--color-primary)]/30"
                >
                  <h3 className="font-semibold text-[var(--color-text-primary)] text-sm leading-snug">
                    {faq.q}
                  </h3>
                  <p className="mt-2 text-sm text-[var(--color-text-secondary)] leading-relaxed">
                    {faq.a}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </PublicLayout>
  );
}
