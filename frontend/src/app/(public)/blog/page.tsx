import { Metadata } from "next";
import Link from "next/link";

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
    <div className="page-transition-enter">
      {/* Hero */}
      <section className="relative overflow-hidden py-16 lg:py-24">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-1/2 -right-1/4 h-[600px] w-[600px] rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
        </div>
        <div className="relative container-grid">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-5xl">
              Market <span className="text-[var(--color-primary)]">Insights</span> Blog
            </h1>
            <p className="mt-6 text-lg text-[var(--color-text-secondary)]">
              Stay ahead of the markets with our latest analysis, trading strategies, and industry insights from our team of experts.
            </p>
          </div>
        </div>
      </section>

      {/* Featured Post */}
      <section className="py-8 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="rounded-2xl border border-[var(--color-primary)]/30 bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent p-8 lg:p-12">
            <span className="inline-flex items-center rounded-full bg-[var(--color-primary)]/10 px-3 py-1 text-xs font-medium text-[var(--color-primary)]">
              Featured
            </span>
            <h2 className="mt-4 text-2xl font-bold text-[var(--color-text-primary)] lg:text-3xl">
              {blogPosts[0].title}
            </h2>
            <p className="mt-3 text-[var(--color-text-secondary)] max-w-3xl">
              {blogPosts[0].excerpt}
            </p>
            <div className="mt-6 flex items-center gap-4 text-sm text-[var(--color-text-secondary)]">
              <span>{blogPosts[0].author}</span>
              <span>•</span>
              <span>{blogPosts[0].date}</span>
              <span>•</span>
              <span>{blogPosts[0].readTime}</span>
            </div>
            <Link
              href={`/blog/${blogPosts[0].id}`}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-[var(--color-primary-hover)]"
            >
              Read Article
              <span className="text-lg">→</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Blog Grid */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {blogPosts.slice(1).map((post, index) => (
              <article
                key={index}
                className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden shadow-sm transition-all hover:border-[var(--color-primary)]/50 hover:shadow-lg"
              >
                <div className="aspect-video bg-gradient-to-br from-[var(--color-primary)]/10 to-[var(--color-border)]/50 flex items-center justify-center">
                  <span className="text-4xl opacity-50">📝</span>
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
                    <span className="rounded-full bg-[var(--color-primary)]/10 px-2 py-1 text-[var(--color-primary)]">
                      {post.category}
                    </span>
                    <span>•</span>
                    <span>{post.readTime}</span>
                  </div>
                  <h3 className="mt-3 text-lg font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-primary)] transition-colors">
                    {post.title}
                  </h3>
                  <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                    {post.excerpt}
                  </p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {post.author} • {post.date}
                    </span>
                    <Link
                      href={`/blog/${post.id}`}
                      className="text-sm font-medium text-[var(--color-primary)] hover:underline"
                    >
                      Read more
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-16 border-t border-[var(--color-border)]">
        <div className="container-grid">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 lg:p-12 text-center">
            <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">
              Subscribe to Our Newsletter
            </h2>
            <p className="mt-3 text-[var(--color-text-secondary)] max-w-xl mx-auto">
              Get the latest market insights, trading strategies, and product updates delivered straight to your inbox.
            </p>
            <form className="mt-6 flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[#64748b] focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
              />
              <button
                type="submit"
                className="rounded-lg bg-[var(--color-primary)] px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--color-primary-hover)]"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
      </section>
    </div>
  );
}
