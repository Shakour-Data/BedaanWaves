"""Alerts API Router
---------------------------------------------------------------------------
API endpoints for managing user alerts and notifications.

FEATURES:
- Price alerts (above/below threshold)
- Score change alerts (dimension scores)
- Volume spike alerts
- News/sentiment alerts
- Technical indicator alerts (RSI, MACD, etc.)
- Multi-channel delivery (in-app, email, webhook)

USAGE:
- POST /api/v1/alerts - Create new alert
- GET /api/v1/alerts - List user alerts
- GET /api/v1/alerts/{alert_id} - Get alert details
- PUT /api/v1/alerts/{alert_id} - Update alert
- DELETE /api/v1/alerts/{alert_id} - Delete alert
- POST /api/v1/alerts/{alert_id}/toggle - Enable/disable alert
- GET /api/v1/alerts/history - Get triggered alerts history
- POST /api/v1/alerts/bulk - Create multiple alerts
"""

from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator

from ....core.config import get_settings
from ....services.user.auth_service import AuthService, get_current_user
from ....services.notifications.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# =============================================================================
# Enums and Types
# =============================================================================

class AlertType(str, Enum):
    """Types of alerts supported by the system"""
    PRICE_ABOVE = "price_above"           # Price goes above threshold
    PRICE_BELOW = "price_below"           # Price goes below threshold
    PRICE_CHANGE_PCT = "price_change_pct"  # Price changes by percentage
    VOLUME_SPIKE = "volume_spike"         # Volume spikes above threshold
    SCORE_CHANGE = "score_change"         # Dimension score changes
    RATING_UPGRADE = "rating_upgrade"     # Stock rating upgrades
    RATING_DOWNGRADE = "rating_downgrade" # Stock rating downgrades
    RSI_OVERBOUGHT = "rsi_overbought"     # RSI indicates overbought
    RSI_OVERSOLD = "rsi_oversold"         # RSI indicates oversold
    MACD_SIGNAL = "macd_signal"           # MACD generates signal
    NEWS_SENTIMENT = "news_sentiment"       # News sentiment changes
    SECTOR_MOMENTUM = "sector_momentum"   # Sector momentum shifts


class AlertStatus(str, Enum):
    """Status of an alert"""
    ACTIVE = "active"           # Alert is enabled and monitoring
    PAUSED = "paused"           # Alert is temporarily disabled
    TRIGGERED = "triggered"     # Alert has been triggered
    EXPIRED = "expired"         # Alert has expired
    DISABLED = "disabled"       # Alert is permanently disabled


class DeliveryChannel(str, Enum):
    """Channels for alert delivery"""
    IN_APP = "in_app"           # In-app notification
    EMAIL = "email"             # Email notification
    WEBHOOK = "webhook"         # Webhook callback
    SMS = "sms"                 # SMS notification (if configured)
    PUSH = "push"               # Push notification (mobile)


# =============================================================================
# Request/Response Models
# =============================================================================

class PriceThreshold(BaseModel):
    """Price threshold condition"""
    value: float = Field(..., description="Price threshold value")
    currency: str = Field("USD", description="Currency code")


class PercentageThreshold(BaseModel):
    """Percentage change threshold"""
    value: float = Field(..., ge=0, le=100, description="Percentage threshold")
    timeframe: str = Field("1d", description="Timeframe (1d, 1w, 1m)")


class VolumeThreshold(BaseModel):
    """Volume spike threshold"""
    multiplier: float = Field(..., ge=1.5, description="Volume multiplier vs average")
    avg_period: int = Field(20, ge=5, description="Period for average calculation")


class ScoreThreshold(BaseModel):
    """Dimension score threshold"""
    dimension: str = Field(..., description="Dimension name (fundamental, technical, etc.)")
    threshold: float = Field(..., ge=0, le=100, description="Score threshold (0-100)")
    direction: str = Field("above", description="Trigger when score goes 'above' or 'below'")


class TechnicalIndicatorThreshold(BaseModel):
    """Technical indicator threshold"""
    indicator: str = Field(..., description="Indicator name (rsi, macd, etc.)")
    threshold: float = Field(..., description="Indicator threshold value")
    direction: str = Field("above", description="Trigger direction")


class AlertCondition(BaseModel):
    """Alert condition configuration"""
    type: AlertType = Field(..., description="Type of alert condition")
    
    # One of these should be provided based on alert type
    price_threshold: Optional[PriceThreshold] = None
    percentage_threshold: Optional[PercentageThreshold] = None
    volume_threshold: Optional[VolumeThreshold] = None
    score_threshold: Optional[ScoreThreshold] = None
    technical_threshold: Optional[TechnicalIndicatorThreshold] = None
    
    @validator('*', pre=True)
    def validate_thresholds(cls, v, values):
        """Ensure at least one threshold is provided"""
        alert_type = values.get('type')
        if alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW] and not values.get('price_threshold'):
            raise ValueError('price_threshold required for price alerts')
        return v


class DeliverySettings(BaseModel):
    """Alert delivery configuration"""
    channels: List[DeliveryChannel] = Field(default=[DeliveryChannel.IN_APP])
    email_address: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_headers: Optional[dict] = None


class CreateAlertRequest(BaseModel):
    """Request to create a new alert"""
    name: str = Field(..., min_length=1, max_length=100, description="Alert name")
    description: Optional[str] = Field(None, max_length=500)
    symbols: List[str] = Field(..., min_items=1, max_items=10, description="Symbols to monitor")
    condition: AlertCondition = Field(..., description="Alert condition")
    delivery: DeliverySettings = Field(default_factory=DeliverySettings)
    cooldown_minutes: int = Field(60, ge=0, description="Cooldown between triggers (minutes)")
    expires_at: Optional[datetime] = None
    is_active: bool = Field(True)


class UpdateAlertRequest(BaseModel):
    """Request to update an existing alert"""
    name: Optional[str] = None
    description: Optional[str] = None
    symbols: Optional[List[str]] = None
    condition: Optional[AlertCondition] = None
    delivery: Optional[DeliverySettings] = None
    cooldown_minutes: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Alert response model"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    symbols: List[str]
    condition: AlertCondition
    delivery: DeliverySettings
    status: AlertStatus
    cooldown_minutes: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    trigger_count: int


class AlertHistoryEntry(BaseModel):
    """Single alert trigger history entry"""
    id: str
    alert_id: str
    triggered_at: datetime
    symbol: str
    condition_type: AlertType
    threshold_value: float
    actual_value: float
    message: str
    delivered_via: List[DeliveryChannel]
    delivery_status: str  # success, failed, pending


class AlertHistoryResponse(BaseModel):
    """Alert history response"""
    status: str
    count: int
    page: int
    per_page: int
    total_pages: int
    entries: List[AlertHistoryEntry]


class BulkCreateAlertsRequest(BaseModel):
    """Request to create multiple alerts at once"""
    alerts: List[CreateAlertRequest] = Field(..., min_items=1, max_items=10)


class BulkCreateAlertsResponse(BaseModel):
    """Response for bulk alert creation"""
    status: str
    created_count: int
    failed_count: int
    alerts: List[AlertResponse]
    errors: List[dict]  # For failed creations


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    request: CreateAlertRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """
    Create a new alert for monitoring stocks.
    
    Supports multiple alert types including price thresholds, 
    score changes, volume spikes, and technical indicators.
    """
    try:
        alert = await alert_service.create_alert(
            user_id=current_user["id"],
            request=request,
        )
        
        # Schedule background task for immediate check
        background_tasks.add_task(
            alert_service.check_alert_immediately,
            alert.id
        )
        
        return alert
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """
    List all alerts for the current user with optional filtering.
    
    Supports filtering by status, symbol, and alert type.
    """
    try:
        alerts = await alert_service.list_alerts(
            user_id=current_user["id"],
            status=status,
            symbol=symbol,
            alert_type=alert_type,
            page=page,
            per_page=per_page,
        )
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Get details of a specific alert"""
    try:
        alert = await alert_service.get_alert(
            alert_id=alert_id,
            user_id=current_user["id"],
        )
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    request: UpdateAlertRequest,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Update an existing alert"""
    try:
        alert = await alert_service.update_alert(
            alert_id=alert_id,
            user_id=current_user["id"],
            request=request,
        )
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Delete an alert"""
    try:
        success = await alert_service.delete_alert(
            alert_id=alert_id,
            user_id=current_user["id"],
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alert_id}/toggle", response_model=AlertResponse)
async def toggle_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Toggle alert active status"""
    try:
        alert = await alert_service.toggle_alert(
            alert_id=alert_id,
            user_id=current_user["id"],
        )
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
            
        return alert
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=AlertHistoryResponse)
async def get_alert_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    alert_type: Optional[AlertType] = Query(None, description="Filter by alert type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Get history of triggered alerts"""
    try:
        history = await alert_service.get_alert_history(
            user_id=current_user["id"],
            symbol=symbol,
            alert_type=alert_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )
        return history
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk", response_model=BulkCreateAlertsResponse)
async def create_alerts_bulk(
    request: BulkCreateAlertsRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """
    Create multiple alerts in bulk.
    
    Useful for setting up a complete watchlist with various alert types.
    """
    try:
        result = await alert_service.create_alerts_bulk(
            user_id=current_user["id"],
            alerts=request.alerts,
        )
        
        # Schedule checks for all new alerts
        for alert in result.alerts:
            background_tasks.add_task(
                alert_service.check_alert_immediately,
                alert.id
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Utility Endpoints
# =============================================================================

@router.get("/types", response_model=List[dict])
async def get_alert_types():
    """Get list of available alert types with descriptions"""
    return [
        {
            "type": AlertType.PRICE_ABOVE,
            "name": "Price Above",
            "description": "Trigger when price goes above specified value",
            "requires": ["price_threshold"]
        },
        {
            "type": AlertType.PRICE_BELOW,
            "name": "Price Below",
            "description": "Trigger when price goes below specified value",
            "requires": ["price_threshold"]
        },
        {
            "type": AlertType.SCORE_CHANGE,
            "name": "Score Change",
            "description": "Trigger when dimension score changes significantly",
            "requires": ["score_threshold"]
        },
        {
            "type": AlertType.VOLUME_SPIKE,
            "name": "Volume Spike",
            "description": "Trigger when volume spikes above average",
            "requires": ["volume_threshold"]
        },
        {
            "type": AlertType.RSI_OVERBOUGHT,
            "name": "RSI Overbought",
            "description": "Trigger when RSI indicates overbought conditions",
            "requires": []
        },
        {
            "type": AlertType.RSI_OVERSOLD,
            "name": "RSI Oversold",
            "description": "Trigger when RSI indicates oversold conditions",
            "requires": []
        },
    ]


@router.get("/stats", response_model=dict)
async def get_alert_stats(
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(),
):
    """Get alert statistics for the current user"""
    try:
        stats = await alert_service.get_user_alert_stats(
            user_id=current_user["id"]
        )
        return {
            "status": "success",
            "user_id": current_user["id"],
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
