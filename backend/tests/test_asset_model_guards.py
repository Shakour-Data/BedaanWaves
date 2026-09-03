"""Tests for the Asset model non-Nasdaq guards.

The Asset model must reject any value of ``market`` other than
``"NASDAQ"`` and any value of ``asset_class`` other than ``"EQUITY"``
or ``"ETF"``. These guards complement the database CHECK constraints
added by the 20260902_purge_non_nasdaq migration.
"""

import pytest

from app.models.models import Asset


def _make_asset(**overrides):
    defaults = dict(
        symbol="TEST",
        name="Test Asset",
        asset_class="EQUITY",
        market="NASDAQ",
    )
    defaults.update(overrides)
    return Asset(**defaults)


def test_asset_accepts_nasdaq_equity():
    a = _make_asset(asset_class="EQUITY", market="NASDAQ")
    assert a.asset_class == "EQUITY"
    assert a.market == "NASDAQ"


def test_asset_accepts_nasdaq_etf():
    a = _make_asset(asset_class="ETF", market="NASDAQ")
    assert a.asset_class == "ETF"


def test_asset_rejects_crypto_asset_class():
    with pytest.raises(ValueError, match="Asset.asset_class"):
        _make_asset(asset_class="CRYPTO")


def test_asset_rejects_index_asset_class():
    with pytest.raises(ValueError, match="Asset.asset_class"):
        _make_asset(asset_class="INDEX")


def test_asset_rejects_commodity_asset_class():
    with pytest.raises(ValueError, match="Asset.asset_class"):
        _make_asset(asset_class="COMMODITY")


def test_asset_rejects_bond_asset_class():
    with pytest.raises(ValueError, match="Asset.asset_class"):
        _make_asset(asset_class="BOND")


def test_asset_rejects_nyse_market():
    with pytest.raises(ValueError, match="Asset.market"):
        _make_asset(market="NYSE")


def test_asset_rejects_binance_market():
    with pytest.raises(ValueError, match="Asset.market"):
        _make_asset(market="BINANCE")


def test_asset_rejects_tse_market():
    with pytest.raises(ValueError, match="Asset.market"):
        _make_asset(market="TSE")


def test_asset_rejects_crypto_market():
    with pytest.raises(ValueError, match="Asset.market"):
        _make_asset(market="CRYPTO")
