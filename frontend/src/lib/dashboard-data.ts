/**
 * dashboard-data.ts
 * ---------------------------------------------------------------------------
 * داده‌های نمایشی داشبورد، با ساختاری هم‌شکل با پاسخ‌های API بک‌اند
 * (برای جایگزینی آسان با apiClient در آینده).
 */

export interface MarketStat {
  label: string;
  value: string;
  changePct?: number;
}

export interface AssetRow {
  symbol: string;
  name: string;
  market: "TSE" | "OTC" | "BINANCE";
  price: number;
  changePct: number;
}

export interface SignalRow {
  symbol: string;
  type: "BUY" | "SELL" | "HOLD";
  confidence: number;
  model: string;
}

export interface NewsItem {
  title: string;
  source: string;
  time: string;
}

export const marketStats: MarketStat[] = [
  { label: "شاخص کل", value: "۲٬۱۸۴٬۵۳۰", changePct: 1.24 },
  { label: "ارزش معاملات", value: "۱۲٬۴۸۰ میلیارد", changePct: -0.42 },
  { label: "حجم معاملات", value: "۸٬۹۱۰ میلیون", changePct: 2.05 },
  { label: "نمادهای مثبت", value: "۲۴۷", changePct: 3.1 },
];

export const topMovers: AssetRow[] = [
  { symbol: "فولاد", name: "فولاد مبارکه اصفهان", market: "TSE", price: 5840, changePct: 4.92 },
  { symbol: "شستا", name: "سرمایه‌گذاری تامین اجتماعی", market: "TSE", price: 1320, changePct: 4.31 },
  { symbol: "خودرو", name: "ایران خودرو", market: "TSE", price: 2980, changePct: -3.78 },
  { symbol: "وبملت", name: "بانک ملت", market: "TSE", price: 6710, changePct: 2.14 },
  { symbol: "فملی", name: "ملی صنایع مس ایران", market: "TSE", price: 12450, changePct: -1.96 },
  { symbol: "BTC", name: "Bitcoin", market: "BINANCE", price: 68420, changePct: 2.83 },
];

export const watchlist: AssetRow[] = [
  { symbol: "شپنا", name: "پالایش نفت اصفهان", market: "TSE", price: 4120, changePct: 1.12 },
  { symbol: "فارس", name: "صنایع پتروشیمی خلیج فارس", market: "TSE", price: 9980, changePct: 0.64 },
  { symbol: "ETH", name: "Ethereum", market: "BINANCE", price: 3580, changePct: -2.21 },
  { symbol: "ونوک", name: "ونوک", market: "OTC", price: 1540, changePct: 5.04 },
];

export const signals: SignalRow[] = [
  { symbol: "فولاد", type: "BUY", confidence: 87.4, model: "ScoringService-6D" },
  { symbol: "فملی", type: "HOLD", confidence: 62.1, model: "MomentumService" },
  { symbol: "خودرو", type: "SELL", confidence: 78.9, model: "RiskAnalysisService" },
  { symbol: "BTC", type: "BUY", confidence: 71.5, model: "CryptoAnalysisService" },
];

export const news: NewsItem[] = [
  { title: "رشد تقاضا در گروه فلزات اساسی پس از اعلام نرخ تسعیر", source: "بورس‌نیوز", time: "۱۲ دقیقه پیش" },
  { title: "تحلیل ۶ بعدی: فولاد در موج حمایتی قرار گرفت", source: "بیدان‌ویوز", time: "۳۴ دقیقه پیش" },
  { title: "نوسان بیت‌کوین در کانال ۶۸ هزار دلار ادامه دارد", source: "کوین‌دسک", time: "۱ ساعت پیش" },
];
