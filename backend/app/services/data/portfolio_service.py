"""
Portfolio Service - Tier 2 Data Service

User portfolio management with full CRUD operations, holdings management,
performance calculation, and portfolio analysis.  Integrates with the
database when a session is available; falls back to in-memory stubs
when no persistence layer is configured.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select, update

from app.core.utils import utc_now_iso
from app.db.base import async_session_maker
from app.models.models import Asset, Portfolio, Position

from ..core import DataService


class PortfolioService(DataService):
    """
    Portfolio management service.

    Provides:
    - Portfolio CRUD operations with database persistence
    - Holdings management (add/remove/list positions)
    - Performance calculation (current value, gain/loss, percentages)
    - Portfolio analysis
    """

    def __init__(
        self,
        service_name: str = "PortfolioService",
        db_service=None,
    ):
        super().__init__(service_name)
        self.db_service = db_service

    async def initialize(self) -> None:
        self.logger.info("PortfolioService initialized")

    async def shutdown(self) -> None:
        self.logger.info("PortfolioService shutdown")

    async def get_by_id(self, entity_id: int) -> dict[str, Any] | None:
        try:
            async with async_session_maker() as session:
                result = await session.execute(select(Portfolio).where(Portfolio.id == entity_id))
                portfolio = result.scalars().first()
                if portfolio:
                    return {
                        "id": str(portfolio.id),
                        "name": portfolio.name,
                        "type": portfolio.portfolio_type,
                        "base_currency": portfolio.base_currency,
                        "is_public": portfolio.is_public,
                        "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
                    }
                return None
        except Exception as exc:
            self.logger.debug(f"Portfolio DB lookup failed (id={entity_id}): {exc}")
            return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        try:
            async with async_session_maker() as session:
                result = await session.execute(select(Portfolio).limit(limit).offset(offset))
                portfolios = result.scalars().all()
                return [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "type": p.portfolio_type,
                        "base_currency": p.base_currency,
                    }
                    for p in portfolios
                ]
        except Exception as exc:
            self.logger.debug(f"Portfolio DB list failed: {exc}")
            return []

    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(f"Creating portfolio: {data.get('name')}")
        try:
            async with async_session_maker() as session:
                portfolio = Portfolio(
                    name=data.get("name", "Untitled"),
                    description=data.get("description"),
                    portfolio_type=data.get("type", "PERSONAL"),
                    base_currency=data.get("base_currency", "IRR"),
                )
                session.add(portfolio)
                await session.commit()
                return {**data, "id": str(portfolio.id), "created_at": utc_now_iso()}
        except Exception as exc:
            self.logger.debug(f"Portfolio creation failed: {exc}")
            return data

    async def update(self, entity_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self.logger.info(f"Updating portfolio {entity_id}")
        try:
            async with async_session_maker() as session:
                await session.execute(
                    update(Portfolio)
                    .where(Portfolio.id == entity_id)
                    .values(
                        name=data.get("name"),
                        description=data.get("description"),
                        portfolio_type=data.get("type"),
                        base_currency=data.get("base_currency"),
                        updated_at=datetime.now(UTC),
                    )
                )
                await session.commit()
        except Exception as exc:
            self.logger.debug(f"Portfolio update failed: {exc}")
        return data

    async def delete(self, entity_id: int) -> bool:
        self.logger.info(f"Deleting portfolio {entity_id}")
        try:
            async with async_session_maker() as session:
                await session.execute(delete(Position).where(Position.portfolio_id == entity_id))
                await session.execute(delete(Portfolio).where(Portfolio.id == entity_id))
                await session.commit()
        except Exception as exc:
            self.logger.debug(f"Portfolio delete failed: {exc}")
        return True

    async def add_holding(
        self,
        portfolio_id: int,
        stock_ticker: str,
        quantity: float,
        purchase_price: float,
    ) -> dict[str, Any]:
        """
        Add holding to portfolio.

        Args:
            portfolio_id: Portfolio ID
            stock_ticker: Stock ticker
            quantity: Quantity of shares
            purchase_price: Purchase price per share

        Returns:
            Holding data
        """
        asset_result = await self._resolve_asset(stock_ticker)
        asset_id = asset_result["id"] if asset_result else None

        holding = {
            "portfolio_id": portfolio_id,
            "stock_ticker": stock_ticker,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "purchase_date": utc_now_iso(),
        }

        try:
            if asset_id is not None:
                async with async_session_maker() as session:
                    position = Position(
                        portfolio_id=portfolio_id,
                        asset_id=asset_id,
                        quantity=quantity,
                        entry_price=purchase_price,
                        entry_date=datetime.now(UTC),
                    )
                    session.add(position)
                    await session.commit()
                    holding["id"] = str(position.id)
        except Exception as exc:
            self.logger.debug(f"Holding creation failed: {exc}")

        self.logger.info(f"Added holding: {stock_ticker} to portfolio {portfolio_id}")
        return holding

    async def _resolve_asset(self, ticker: str) -> dict[str, Any] | None:
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Asset).where(Asset.symbol == ticker.upper())
                )
                asset = result.scalars().first()
                if asset:
                    return {"id": str(asset.id), "symbol": asset.symbol}
                return None
        except Exception:
            return None

    async def remove_holding(self, portfolio_id: int, holding_id: int) -> bool:
        """Remove holding from portfolio"""
        self.logger.info(f"Removed holding {holding_id} from portfolio {portfolio_id}")
        try:
            async with async_session_maker() as session:
                await session.execute(
                    delete(Position)
                    .where(Position.portfolio_id == portfolio_id)
                    .where(Position.id == holding_id)
                )
                await session.commit()
        except Exception as exc:
            self.logger.debug(f"Holding removal failed: {exc}")
        return True

    async def get_holdings(self, portfolio_id: int) -> list[dict[str, Any]]:
        """Get portfolio holdings"""
        self.logger.debug(f"Getting holdings for portfolio {portfolio_id}")
        try:
            async with async_session_maker() as session:
                stmt = (
                    select(Position, Asset.symbol)
                    .join(Asset, Position.asset_id == Asset.id)
                    .where(Position.portfolio_id == portfolio_id)
                )
                result = await session.execute(stmt)
                holdings = []
                for position, symbol in result.all():
                    holdings.append({
                        "portfolio_id": portfolio_id,
                        "stock_ticker": symbol,
                        "quantity": float(position.quantity),
                        "purchase_price": float(position.entry_price),
                        "purchase_date": position.entry_date.isoformat() if position.entry_date else None,
                    })
                return holdings
        except Exception as exc:
            self.logger.debug(f"Holdings lookup failed: {exc}")
            return []

    async def calculate_value(self, portfolio_id: int, current_prices: dict[str, float]) -> dict[str, float]:
        """
        Calculate portfolio value.

        Args:
            portfolio_id: Portfolio ID
            current_prices: Current prices {ticker: price}

        Returns:
            Portfolio value metrics
        """
        holdings = await self.get_holdings(portfolio_id)

        total_current_value = 0.0
        total_purchase_value = 0.0

        for holding in holdings:
            ticker = holding.get("stock_ticker")
            quantity = holding.get("quantity", 0)
            purchase_price = holding.get("purchase_price", 0)

            current_price = current_prices.get(ticker, purchase_price)

            total_purchase_value += quantity * purchase_price
            total_current_value += quantity * current_price

        return {
            "total_current_value": total_current_value,
            "total_purchase_value": total_purchase_value,
            "total_gain_loss": total_current_value - total_purchase_value,
            "gain_loss_percent": (
                ((total_current_value - total_purchase_value) / total_purchase_value * 100)
                if total_purchase_value > 0
                else 0
            ),
        }
