"""
Unit tests for the Nasdaq ranking scoring helpers.
Validates grade assignment and the technical/risk dimension scoring math.
"""
import unittest

from app.api.routes.ranking import _assign_grade, _technical_score, _risk_score


class TestAssignGrade(unittest.TestCase):
    def test_strong_buy(self):
        self.assertEqual(_assign_grade(90), "A_STRONG_BUY")

    def test_buy_boundary(self):
        self.assertEqual(_assign_grade(70), "B_BUY")

    def test_hold_boundary(self):
        self.assertEqual(_assign_grade(55), "C_HOLD")

    def test_sell_boundary(self):
        self.assertEqual(_assign_grade(40), "D_SELL")

    def test_strong_sell(self):
        self.assertEqual(_assign_grade(10), "E_STRONG_SELL")

    def test_exact_threshold(self):
        self.assertEqual(_assign_grade(85), "A_STRONG_BUY")
        self.assertEqual(_assign_grade(54.9), "D_SELL")


class TestTechnicalScore(unittest.TestCase):
    def test_insufficient_data(self):
        self.assertEqual(_technical_score([100.0]), 0.0)

    def test_strong_uptrend(self):
        closes = [100.0] * 19 + [200.0]
        self.assertEqual(_technical_score(closes), 100.0)

    def test_strong_downtrend(self):
        closes = [100.0] * 19 + [50.0]
        self.assertEqual(_technical_score(closes), 0.0)

    def test_flat(self):
        closes = [100.0] * 21
        self.assertEqual(_technical_score(closes), 50.0)


class TestRiskScore(unittest.TestCase):
    def test_insufficient_data(self):
        self.assertEqual(_risk_score([100.0]), 50.0)

    def test_low_volatility(self):
        closes = [100.0 + i * 0.01 for i in range(30)]
        score = _risk_score(closes)
        self.assertGreater(score, 90.0)
        self.assertLessEqual(score, 100.0)

    def test_high_volatility(self):
        closes = [100.0, 180.0, 60.0, 170.0, 50.0, 160.0, 40.0, 150.0, 45.0]
        score = _risk_score(closes)
        self.assertLessEqual(score, 5.0)
        self.assertGreaterEqual(score, 0.0)
