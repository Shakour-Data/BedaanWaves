import Link from "next/link";
import { PrimaryButton } from "@/components/ui/PrimaryButton";

const features = [
  {
    title: "Nasdaq Market Data",
    desc: "Real-time and historical price data for Nasdaq Composite and all constituents",
  },
  {
    title: "Fundamental Analysis",
    desc: "Quarterly financial statements, ratios, and key metrics for US equities",
  },
  {
    title: "AI-Powered Signals",
    desc: "Machine learning predictions and technical analysis for informed decisions",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <section className="px-4 pt-10 pb-6">
        <h1 className="text-center text-4xl font-bold text-gray-800 mb-4">
          BedaanWaves - Nasdaq Market Analysis Platform
        </h1>
        <p className="text-center text-gray-600 text-lg mb-12 max-w-2xl mx-auto">
          Comprehensive market analysis and AI trading platform focused on
          Nasdaq Composite index and its constituents. 5 years of historical data,
          fundamentals, and AI signals.
        </p>
      </section>

      <section className="px-4 pb-12">
        <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
          Key Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {features.map((item) => (
            <div
              key={item.title}
              className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
            >
              <h3 className="text-xl font-semibold text-blue-700 mb-2">
                {item.title}
              </h3>
              <p className="text-gray-600 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 pb-12 text-center">
        <div className="flex flex-col items-center gap-4">
          <Link href="/stocks">
            <PrimaryButton>View Nasdaq Stocks</PrimaryButton>
          </Link>
          <p className="text-gray-400 text-sm">
            Backend running on port 3000 | Frontend on port 3005
          </p>
        </div>
      </section>
    </main>
  );
}
