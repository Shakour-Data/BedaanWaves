import Link from "next/link";

export default function AuthRouteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-3/5 relative bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 h-96 w-96 rounded-full bg-white" />
          <div className="absolute top-1/2 -left-20 h-72 w-72 rounded-full bg-white" />
          <div className="absolute -bottom-20 right-1/4 h-80 w-80 rounded-full bg-white" />
        </div>
        <div className="relative z-10 flex flex-col justify-between p-12 xl:p-16 text-white">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <span className="text-white font-bold text-xl">B</span>
            </div>
            <span className="text-xl font-bold">BedaanWaves</span>
          </Link>

          <div className="max-w-lg">
            <h2 className="text-3xl xl:text-4xl font-bold leading-tight mb-6 text-balance">
              Master the Markets with AI-Powered Analytics
            </h2>
            <p className="text-lg text-white/80 leading-relaxed">
              Join thousands of traders who use BedaanWaves for professional-grade market analysis, real-time data, and intelligent scoring.
            </p>
            <div className="mt-8 flex items-center gap-6">
              <div className="flex -space-x-3">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="h-10 w-10 rounded-full border-2 border-white/30 bg-white/20 flex items-center justify-center text-xs font-bold text-white"
                  >
                    {String.fromCharCode(64 + i)}
                  </div>
                ))}
              </div>
              <div className="text-sm text-white/80">
                <span className="font-semibold text-white">5,000+</span> traders already onboard
              </div>
            </div>
          </div>

          <div className="text-sm text-white/60">
            © 2026 BedaanWaves. All rights reserved.
          </div>
        </div>
      </div>

      {/* Right side - Auth form */}
      <div className="flex w-full lg:w-1/2 xl:w-2/5 items-center justify-center p-6 sm:p-8 bg-[var(--color-background)]">
        <div className="w-full max-w-md">
          <div className="lg:hidden text-center mb-8">
            <Link href="/" className="inline-flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)]">
                <span className="text-white font-bold text-sm">B</span>
              </div>
              <span className="text-lg font-bold text-[var(--color-text-primary)]">BedaanWaves</span>
            </Link>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
