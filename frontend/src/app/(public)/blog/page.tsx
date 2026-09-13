import { Metadata } from "next";
import Link from "next/link";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { ArrowRight, Calendar, Clock, User, Tag } from "lucide-react";

export const metadata: Metadata = {
  title: "Blog | BedaanWaves",
  description: "Latest insights, market analysis, and trading strategies from the BedaanWaves team.",
};

const blogPosts = [
  {
    id: 1,
    title: "The Future of AI in Stock Market Analysis",
    excerpt:
      "How machine learning is transforming the way traders analyze markets and make decisions.",
    date: "Aug 25, 2026",
    readTime: "8 min read",
    category: "AI & Technology",
    author: "Emily Davis",
  },
  {
    id: 2,
    title: "Understanding Market Volatility in 2026",
    excerpt:
      "A deep dive into current market conditions and strategies for navigating volatile periods.",
    date: "Aug 22, 2026",
    readTime: "6 min read",
    category: "Market Analysis",
    author: "Alex Chen",
  },
  {
    id: 3,
    title: "Building a Robust Trading Strategy with Technical Indicators",
    excerpt:
      "Combine multiple technical indicators to create a comprehensive trading strategy that adapts to market conditions.",
    date: "Aug 18, 2026",
    readTime: "10 min read",
    category: "Trading Strategies",
    author: "Michael Park",
  },
  {
    id: 4,
    title: "Portfolio Diversification: Beyond the Basics",
    excerpt:
      "Advanced techniques for building a resilient portfolio that weathers market storms.",
    date: "Aug 15, 2026",
    readTime: "7 min read",
    category: "Portfolio Management",
    author: "Sarah Johnson",
  },
  {
    id: 5,
    title: "The Rise of Retail Trading in the Digital Age",
    excerpt:
      "How technology has empowered individual traders and changed the landscape of financial markets.",
    date: "Aug 10, 2026",
    readTime: "5 min read",
    category: "Industry Trends",
    author: "Alex Chen",
  },
  {
    id: 6,
    title: "Mastering Risk Management in 2026",
    excerpt:
      "Essential risk management techniques every trader should know to protect their capital.",
    date: "Aug 5, 2026",
    readTime: "9 min read",
    category: "Risk Management",
    author: "Emily Davis",
  },
];

export default function BlogPage() {
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
                <span className="text-sm font-medium text-[var(--color-primary)]">Latest Insights</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl text-balance">
                Market <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">Insights</span> Blog
              </h1>
              <p className="mt-8 text-lg text-[var(--color-text-secondary)] leading-relaxed max-w-2xl">
                Stay ahead of the markets with our latest analysis, trading strategies, and industry insights from our team of experts.
              </p>
            </div>
          </div>
        </section>

        {/* Featured Post */}
        <section className="py-8 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="group relative overflow-hidden rounded-2xl border border-[var(--color-primary)]/30 bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent p-8 lg:p-12 transition-all hover:shadow-lg hover:border-[var(--color-primary)]/50">
              <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-[var(--color-primary)]/10 to-transparent rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500" />
              <span className="relative inline-flex items-center rounded-full bg-[var(--color-primary)]/10 px-3 py-1 text-xs font-semibold text-[var(--color-primary)]">
                Featured
              </span>
              <h2 className="relative mt-4 text-2xl font-bold text-[var(--color-text-primary)] lg:text-3xl group-hover:text-[var(--color-primary)] transition-colors">
                {blogPosts[0].title}
              </h2>
              <p className="relative mt-3 text-[var(--color-text-secondary)] max-w-3xl leading-relaxed">
                {blogPosts[0].excerpt}
              </p>
              <div className="relative mt-6 flex flex-wrap items-center gap-4 text-sm text-[var(--color-text-secondary)]">
                <span className="flex items-center gap-1.5"><User className="h-4 w-4" />{blogPosts[0].author}</span>
                <span className="flex items-center gap-1.5"><Calendar className="h-4 w-4" />{blogPosts[0].date}</span>
                <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" />{blogPosts[0].readTime}</span>
              </div>
              <Link
                href={`/blog/${blogPosts[0].id}`}
                className="relative mt-6 inline-flex items-center gap-2 rounded-xl bg-[var(--color-primary)] px-6 py-3 text-sm font-semibold text-white shadow-lg transition-all hover:bg-[var(--color-primary-hover)] hover:shadow-xl hover:-translate-y-0.5"
              >
                Read Article
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* Blog Grid */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {blogPosts.slice(1).map((post, index) => (
                <article
                  key={index}
                  className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-xl hover:-translate-y-1"
                >
                  <div className="aspect-video bg-gradient-to-br from-[var(--color-primary)]/10 to-[var(--color-border)]/50 flex items-center justify-center relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <span className="text-5xl opacity-40 group-hover:scale-110 transition-transform duration-300">📝</span>
                  </div>
                  <div className="p-6">
                    <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)] mb-3">
                      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-primary-soft)] px-2.5 py-1 text-[var(--color-primary)] font-medium">
                        <Tag className="h-3 w-3" />
                        {post.category}
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{post.readTime}</span>
                    </div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)] transition-colors leading-snug">
                      {post.title}
                    </h3>
                    <p className="mt-2 text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      {post.excerpt}
                    </p>
                    <div className="mt-4 flex items-center justify-between">
                      <span className="text-xs text-[var(--color-text-muted)]">
                        {post.author} • {post.date}
                      </span>
                      <Link
                        href={`/blog/${post.id}`}
                        className="text-sm font-medium text-[var(--color-primary)] hover:underline inline-flex items-center gap-1 group/link"
                      >
                        Read more
                        <ArrowRight className="h-3 w-3 transition-transform group-hover/link:translate-x-0.5" />
                      </Link>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter */}
        <section className="py-20 border-t border-[var(--color-border)]">
          <div className="container-grid">
            <div className="relative overflow-hidden rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 lg:p-16 text-center">
              <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent" />
              <div className="relative">
                <h2 className="text-2xl font-bold text-[var(--color-text-primary)] sm:text-3xl text-balance">
                  Subscribe to Our Newsletter
                </h2>
                <p className="mt-4 text-[var(--color-text-secondary)] max-w-xl mx-auto leading-relaxed">
                  Get the latest market insights, trading strategies, and product updates delivered straight to your inbox.
                </p>
                <form className="mt-8 flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="flex-1 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/20 transition-all"
                  />
                  <button
                    type="submit"
                    className="rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-[var(--color-primary)]/25 transition-all hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Subscribe
                  </button>
                </form>
              </div>
            </div>
          </div>
        </section>
      </div>
    </PublicLayout>
  );
}
