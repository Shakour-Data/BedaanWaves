export interface StockSearchResult {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  changePct: number;
  marketCap?: number;
}
