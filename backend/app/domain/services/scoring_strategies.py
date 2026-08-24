from abc import ABC, abstractmethod

class IScoringStrategy(ABC):
    @abstractmethod
    def score_rsi(self, value: float) -> float: pass
    
    @abstractmethod
    def score_pe(self, value: float) -> float: pass

class TseScoringStrategy(IScoringStrategy):
    def score_rsi(self, rsi: float) -> float:
        if rsi > 70: return max(0, 100 - (rsi - 70) * 2)
        if rsi < 30: return max(0, 100 - (30 - rsi) * 2)
        return 50 + (rsi - 50) * 0.5

    def score_pe(self, pe: float) -> float:
        if pe <= 0: return 0.0
        if pe < 8: return 90
        if pe < 15: return 75
        return max(0, 100 - pe)

class GlobalScoringStrategy(IScoringStrategy):
    def score_rsi(self, rsi: float) -> float:
        if rsi > 75: return max(0, 100 - (rsi - 75) * 2.5)
        if rsi < 25: return max(0, 100 - (25 - rsi) * 2.5)
        return 50 + (rsi - 50) * 0.5

    def score_pe(self, pe: float) -> float:
        if pe <= 0: return 0.0
        if pe < 10: return 90
        return max(0, 100 - pe)
