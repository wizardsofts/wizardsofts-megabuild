"""
GIBD Quant Calibration Service - FastAPI Application

Provides stock parameter calibration and profiling.
Integrates with Eureka for service discovery.
"""

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import sys
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from profiling.calibrator import StockCalibrator
from database.connection import get_db_context
from database.models import StockProfile
from auth.jwt_validator import get_current_user

# Eureka registration
try:
    from py_eureka_client import eureka_client

    eureka_client.init(
        eureka_server=os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka"),
        app_name=os.getenv("APP_NAME", "gibd-quant-calibration"),
        instance_port=int(os.getenv("APP_PORT", "5003")),
        instance_host=os.getenv("APP_HOST", "gibd-quant-calibration")
    )
except Exception as e:
    print(f"Warning: Eureka registration failed: {e}")

# SECURITY: Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="GIBD Quant Calibration Service",
    description="Stock parameter calibration and profiling",
    version="0.1.0"
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: Input validation patterns
TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,10}$')
VOLATILITY_CATEGORIES = {"LOW", "MEDIUM", "HIGH"}

# SECURITY: API key authentication for write operations
API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for write operations."""
    if not API_KEY:
        return True
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

def validate_ticker(ticker: str) -> str:
    """Validate ticker format."""
    ticker = ticker.upper().strip()
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(status_code=400, detail=f"Invalid ticker format: {ticker}")
    return ticker

# SECURITY: CORS middleware with specific allowed origins
ALLOWED_ORIGINS = [
    "https://wizardsofts.com",
    "https://www.wizardsofts.com",
    "https://guardianinvestmentbd.com",
    "https://www.guardianinvestmentbd.com",
    "https://dailydeenguide.com",
    "https://www.dailydeenguide.com",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:4000",
    "http://localhost:4001",
    "http://localhost:4002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Response models
class ProfileResponse(BaseModel):
    ticker: str
    rsi_overbought: float
    rsi_oversold: float
    volatility_category: str
    typical_volume: float
    high_volume_threshold: float
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    last_calibrated: Optional[str] = None

class CalibrationResponse(BaseModel):
    ticker: str
    status: str
    message: str
    profile: ProfileResponse

@app.get("/health")
@limiter.limit("100/minute")
async def health(request: Request):
    """Health check endpoint"""
    return {"status": "UP", "service": "gibd-quant-calibration"}

@app.post("/api/v1/calibrate/{ticker}", response_model=CalibrationResponse)
@limiter.limit("20/minute")  # SECURITY: Rate limit calibration operations
async def calibrate_stock(
    request: Request,
    ticker: str,
    force: bool = False,
    current_user: dict = Security(get_current_user)
):
    """Auto-calibrate stock parameters from historical data"""
    ticker = validate_ticker(ticker)
    try:
        # Log authenticated request for audit trail
        print(f"Calibration request from user: {current_user.get('email', 'unknown')}")
        calibrator = StockCalibrator()

        with get_db_context() as session:
            # Check if already calibrated
            existing = session.query(StockProfile).filter_by(ticker=ticker).first()

            if existing and not force:
                return CalibrationResponse(
                    ticker=ticker,
                    status="skipped",
                    message="Stock already calibrated. Use force=true to recalibrate.",
                    profile=ProfileResponse(
                        ticker=existing.ticker,
                        rsi_overbought=existing.rsi_overbought,
                        rsi_oversold=existing.rsi_oversold,
                        volatility_category=existing.volatility_category,
                        typical_volume=existing.typical_volume,
                        high_volume_threshold=existing.high_volume_threshold,
                        support_level=existing.support_level,
                        resistance_level=existing.resistance_level,
                        last_calibrated=str(existing.last_calibrated) if existing.last_calibrated else None
                    )
                )

            # Perform calibration
            profile = calibrator.calibrate_stock(ticker, session)

            return CalibrationResponse(
                ticker=ticker,
                status="success",
                message="Stock parameters calibrated successfully",
                profile=ProfileResponse(
                    ticker=profile.ticker,
                    rsi_overbought=profile.rsi_overbought,
                    rsi_oversold=profile.rsi_oversold,
                    volatility_category=profile.volatility_category,
                    typical_volume=profile.typical_volume,
                    high_volume_threshold=profile.high_volume_threshold,
                    support_level=profile.support_level,
                    resistance_level=profile.resistance_level,
                    last_calibrated=str(profile.last_calibrated) if profile.last_calibrated else None
                )
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/calibrate/{ticker}/profile", response_model=ProfileResponse)
@limiter.limit("100/minute")
async def get_stock_profile(
    request: Request,
    ticker: str,
    current_user: dict = Security(get_current_user)
):
    """Get stock profile parameters"""
    ticker = validate_ticker(ticker)
    try:
        # Log authenticated request for audit trail
        print(f"Profile request from user: {current_user.get('email', 'unknown')}")
        with get_db_context() as session:
            profile = session.query(StockProfile).filter_by(ticker=ticker).first()

            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"No profile found for ticker {ticker}. Run calibration first."
                )

            return ProfileResponse(
                ticker=profile.ticker,
                rsi_overbought=profile.rsi_overbought,
                rsi_oversold=profile.rsi_oversold,
                volatility_category=profile.volatility_category,
                typical_volume=profile.typical_volume,
                high_volume_threshold=profile.high_volume_threshold,
                support_level=profile.support_level,
                resistance_level=profile.resistance_level,
                last_calibrated=str(profile.last_calibrated) if profile.last_calibrated else None
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/calibrate/{ticker}/profile", dependencies=[Security(verify_api_key)])
@limiter.limit("30/minute")  # SECURITY: Rate limit profile updates
async def update_stock_profile(
    request: Request,
    ticker: str,
    rsi_overbought: Optional[float] = Field(default=None, ge=50, le=100),
    rsi_oversold: Optional[float] = Field(default=None, ge=0, le=50),
    volatility_category: Optional[str] = None,
    typical_volume: Optional[float] = Field(default=None, ge=0),
    high_volume_threshold: Optional[float] = Field(default=None, ge=0),
    support_level: Optional[float] = Field(default=None, ge=0),
    resistance_level: Optional[float] = Field(default=None, ge=0)
):
    """Manually update stock profile parameters"""
    ticker = validate_ticker(ticker)
    if volatility_category and volatility_category.upper() not in VOLATILITY_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid volatility category. Must be one of: {VOLATILITY_CATEGORIES}")
    try:
        with get_db_context() as session:
            profile = session.query(StockProfile).filter_by(ticker=ticker).first()

            if not profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"No profile found for ticker {ticker}. Run calibration first."
                )

            # Update provided parameters
            if rsi_overbought is not None:
                profile.rsi_overbought = rsi_overbought
            if rsi_oversold is not None:
                profile.rsi_oversold = rsi_oversold
            if volatility_category is not None:
                profile.volatility_category = volatility_category
            if typical_volume is not None:
                profile.typical_volume = typical_volume
            if high_volume_threshold is not None:
                profile.high_volume_threshold = high_volume_threshold
            if support_level is not None:
                profile.support_level = support_level
            if resistance_level is not None:
                profile.resistance_level = resistance_level

            session.commit()
            session.refresh(profile)

            return ProfileResponse(
                ticker=profile.ticker,
                rsi_overbought=profile.rsi_overbought,
                rsi_oversold=profile.rsi_oversold,
                volatility_category=profile.volatility_category,
                typical_volume=profile.typical_volume,
                high_volume_threshold=profile.high_volume_threshold,
                support_level=profile.support_level,
                resistance_level=profile.resistance_level,
                last_calibrated=str(profile.last_calibrated) if profile.last_calibrated else None
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BatchCalibrationRequest(BaseModel):
    tickers: List[str] = Field(..., min_length=1, max_length=100)

    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        validated = []
        for ticker in v:
            ticker = ticker.upper().strip()
            if not TICKER_PATTERN.match(ticker):
                raise ValueError(f'Invalid ticker format: {ticker}')
            validated.append(ticker)
        return validated

@app.post("/api/v1/calibrate/batch")
@limiter.limit("5/minute")  # SECURITY: Rate limit expensive batch operations
async def calibrate_batch(
    request: Request,
    batch_request: BatchCalibrationRequest,
    force: bool = False,
    current_user: dict = Security(get_current_user)
):
    """Calibrate multiple stocks in batch"""
    try:
        # Log authenticated request for audit trail
        print(f"Batch calibration request from user: {current_user.get('email', 'unknown')}")
        calibrator = StockCalibrator()
        results = []

        with get_db_context() as session:
            for ticker in batch_request.tickers:
                try:
                    # Check if already calibrated
                    existing = session.query(StockProfile).filter_by(ticker=ticker).first()

                    if existing and not force:
                        results.append({
                            "ticker": ticker,
                            "status": "skipped",
                            "message": "Already calibrated"
                        })
                        continue

                    # Perform calibration
                    profile = calibrator.calibrate_stock(ticker, session)
                    results.append({
                        "ticker": ticker,
                        "status": "success",
                        "message": "Calibrated successfully"
                    })
                except Exception as e:
                    results.append({
                        "ticker": ticker,
                        "status": "error",
                        "message": str(e)
                    })

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "5003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
