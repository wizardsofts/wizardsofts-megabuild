"""
GIBD Quant Signal Service - FastAPI Application

Provides trading signal generation using AdaptiveSignalEngine.
Integrates with Eureka for service discovery.
"""

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
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

from engine.signal_engine import AdaptiveSignalEngine
from database.connection import get_db_context
from auth.jwt_validator import get_current_user

# Eureka registration
try:
    from py_eureka_client import eureka_client

    eureka_client.init(
        eureka_server=os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka"),
        app_name=os.getenv("APP_NAME", "gibd-quant-signal"),
        instance_port=int(os.getenv("APP_PORT", "5001")),
        instance_host=os.getenv("APP_HOST", "gibd-quant-signal")
    )
except Exception as e:
    print(f"Warning: Eureka registration failed: {e}")

# SECURITY: Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="GIBD Quant Signal Service",
    description="Trading signal generation with adaptive thresholds",
    version="0.1.0"
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: Input validation patterns
TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,10}$')
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

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

# Request/Response models with input validation
class SignalRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    date: Optional[str] = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.upper().strip()
        if not TICKER_PATTERN.match(v):
            raise ValueError(f'Invalid ticker format: {v}')
        return v

class BatchSignalRequest(BaseModel):
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

class SignalResponse(BaseModel):
    ticker: str
    signal_type: str
    total_score: float
    confidence: float
    rsi_score: float
    macd_score: float
    sma_score: float
    adx_score: float
    volume_score: float
    sector_score: float

@app.get("/health")
@limiter.limit("100/minute")
async def health(request: Request):
    """Health check endpoint"""
    return {"status": "UP", "service": "gibd-quant-signal"}

@app.post("/api/v1/signals/generate", response_model=SignalResponse)
@limiter.limit("30/minute")  # SECURITY: Rate limit signal generation
async def generate_signal(
    request: Request,
    signal_request: SignalRequest,
    current_user: dict = Security(get_current_user)
):
    """Generate trading signal for a ticker"""
    try:
        # Log authenticated request for audit trail
        print(f"Signal request from user: {current_user.get('email', 'unknown')}")
        engine = AdaptiveSignalEngine()
        signal = engine.generate_signal(signal_request.ticker, signal_request.date)

        return SignalResponse(
            ticker=signal.ticker,
            signal_type=signal.signal_type,
            total_score=signal.total_score,
            confidence=signal.confidence,
            rsi_score=signal.rsi_score,
            macd_score=signal.macd_score,
            sma_score=signal.sma_score,
            adx_score=signal.adx_score,
            volume_score=signal.volume_score,
            sector_score=signal.sector_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/signals/batch")
@limiter.limit("10/minute")  # SECURITY: Rate limit expensive batch operations
async def generate_batch_signals(
    request: Request,
    batch_request: BatchSignalRequest,
    current_user: dict = Security(get_current_user)
):
    """Generate signals for multiple tickers"""
    try:
        # Log authenticated request for audit trail
        print(f"Batch signal request from user: {current_user.get('email', 'unknown')}")
        engine = AdaptiveSignalEngine()
        results = []

        for ticker in batch_request.tickers:
            try:
                signal = engine.generate_signal(ticker)
                results.append({
                    "ticker": signal.ticker,
                    "signal_type": signal.signal_type,
                    "total_score": signal.total_score,
                    "confidence": signal.confidence
                })
            except Exception as e:
                results.append({
                    "ticker": ticker,
                    "error": str(e)
                })

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/signals/scan")
@limiter.limit("5/minute")  # SECURITY: Rate limit expensive scan operations
async def scan_signals(
    request: Request,
    signal_type: str = Field(default="BUY", pattern="^(BUY|SELL|all)$"),
    threshold: float = Field(default=0.4, ge=0.0, le=1.0),
    limit: int = Field(default=50, ge=1, le=500),
    current_user: dict = Security(get_current_user)
):
    """Scan all stocks for signals"""
    try:
        # Log authenticated request for audit trail
        print(f"Scan signals request from user: {current_user.get('email', 'unknown')}")
        engine = AdaptiveSignalEngine(
            buy_threshold=threshold if signal_type == "BUY" else 0.4,
            sell_threshold=-threshold if signal_type == "SELL" else -0.4
        )

        # Get all active tickers from database
        with get_db_context() as session:
            from database.models import Indicator
            tickers = session.query(Indicator.ticker).distinct().all()
            tickers = [t[0] for t in tickers]

        results = []
        for ticker in tickers[:limit]:  # Limit for performance
            try:
                signal = engine.generate_signal(ticker)
                if signal_type == "all" or signal.signal_type == signal_type:
                    results.append({
                        "ticker": signal.ticker,
                        "signal_type": signal.signal_type,
                        "total_score": signal.total_score,
                        "confidence": signal.confidence
                    })
            except:
                continue

        # Sort by score
        results.sort(key=lambda x: abs(x["total_score"]), reverse=True)
        return {"results": results[:limit]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "5001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
