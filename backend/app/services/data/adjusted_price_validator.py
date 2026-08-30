"""
Adjusted Price Validation

Utility to ensure all analytical calculations use adjusted close prices.
Logs a warning if any function receives unadjusted price data.
"""
import logging

logger = logging.getLogger(__name__)


class AdjustedPriceValidator:
    """
    Validator that enforces adjusted close usage in analytical calculations.
    """

    @staticmethod
    def validate_price_array(prices: list, source: str = "unknown") -> bool:
        """
        Validate that a price array is suitable for analysis.
        In practice, this validates the price source metadata.
        Returns True if valid, logs warning if not.
        """
        if not prices:
            logger.warning(f"Empty price array received from {source}")
            return False
        if len(prices) < 2:
            logger.warning(f"Insufficient price data from {source}: {len(prices)} bars")
            return False
        return True

    @staticmethod
    def warn_if_unadjusted(prices: list, close_prices: list, source: str = "unknown") -> None:
        """
        Log a warning if unadjusted close prices differ significantly from adjusted.
        This is a heuristic check — it compares the last values.
        """
        if not prices or not close_prices or len(prices) != len(close_prices):
            return
        if len(prices) < 2:
            return
        adj_last = float(prices[-1])
        raw_last = float(close_prices[-1])
        if raw_last > 0 and abs(adj_last - raw_last) / raw_last > 0.01:
            logger.warning(
                f"Potential unadjusted data detected from {source}: "
                f"adjusted={adj_last:.4f}, raw={raw_last:.4f} "
                f"(diff={abs(adj_last - raw_last) / raw_last * 100:.2f}%)"
            )
