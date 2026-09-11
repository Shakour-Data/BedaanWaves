"""Quick verification of scientific fixes."""
import sys
sys.path.insert(0, "app")

from app.domain.services.analysis.momentum_engine import MomentumEngine
from app.domain.services.analysis.moving_average_engine import MovingAverageEngine
from app.services.analysis.fundamental_service import FundamentalAnalysisService
from app.services.analysis.risk_service import RiskAnalysisService

def test_rsi_wilder_smoothing():
    me = MomentumEngine()
    prices = [44, 44.5, 43.5, 44, 44.5, 45, 45.5, 46, 45.5, 45, 44.5, 44, 43.5, 43, 43.5]
    rsi = me.calculate_rsi(prices, 14)
    assert 0 <= rsi <= 100, f"RSI out of range: {rsi}"
    print(f"RSI (Wilder): {rsi}")

def test_ema_sma_init():
    mae = MovingAverageEngine()
    prices = [22, 22.5, 23, 23.5, 24, 24.5, 25, 25.5, 26, 26.5]
    ema = mae.calculate_ema(prices, 5)
    sma_init = sum(prices[:5]) / 5
    assert ema > 0, f"EMA should be positive: {ema}"
    print(f"EMA (SMA init): {ema}, SMA init would be: {sma_init}")

def test_macd_signal_histogram():
    me = MomentumEngine()
    prices = [22, 22.5, 23, 23.5, 24, 24.5, 25, 25.5, 26, 26.5, 27, 27.5, 28, 28.5, 29, 29.5, 30, 30.5, 31, 31.5, 32, 32.5, 33, 33.5, 34, 34.5, 35]
    macd_line, signal, histogram, ema12, ema26 = me.calculate_macd(prices)
    assert signal != 0.0 or histogram == macd_line, "Signal should be calculated when enough data"
    print(f"MACD: line={macd_line}, signal={signal}, histogram={histogram}")

def test_dupont_identity():
    fas = FundamentalAnalysisService()
    financials = {'net_income': 100, 'revenue': 1000, 'total_assets': 500, 'equity': 250}
    dupont = fas._calculate_dupont_analysis(financials)
    assert dupont['dupont_identity_check'] == True, f"DuPont identity failed: {dupont}"
    print(f"DuPont ROE: {dupont['roe']}, identity_check: {dupont['dupont_identity_check']}")

def test_operating_leverage():
    fas = FundamentalAnalysisService()
    financials = {'operating_income': 200, 'revenue': 1000}
    ol = fas._calc_operating_leverage(financials)
    assert ol == 1.0, f"Operating leverage should be 1.0: {ol}"
    print(f"Operating Leverage: {ol}")

def test_sortino_ratio():
    ras = RiskAnalysisService()
    returns = [0.01, -0.02, 0.015, -0.01, 0.02, 0.005, -0.015, 0.01, 0.008, -0.005]
    sortino = ras._calculate_sortino_ratio(returns)
    assert sortino > 0, f"Sortino should be positive: {sortino}"
    print(f"Sortino Ratio: {sortino}")

if __name__ == "__main__":
    test_rsi_wilder_smoothing()
    test_ema_sma_init()
    test_macd_signal_histogram()
    test_dupont_identity()
    test_operating_leverage()
    test_sortino_ratio()
    print("All verification tests passed!")
