"""
GIBD Quant NLQ Service - FastAPI Application

Provides natural language query interface for stock analysis.
Integrates with Eureka for service discovery.
"""

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import sys
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlq.api import NLQueryEngine
from database.connection import get_db_context

# Eureka registration
try:
    from py_eureka_client import eureka_client

    eureka_client.init(
        eureka_server=os.getenv("EUREKA_SERVER", "http://localhost:8761/eureka"),
        app_name=os.getenv("APP_NAME", "gibd-quant-nlq"),
        instance_port=int(os.getenv("APP_PORT", "5002")),
        instance_host=os.getenv("APP_HOST", "gibd-quant-nlq")
    )
except Exception as e:
    print(f"Warning: Eureka registration failed: {e}")

# SECURITY: Rate limiting configuration
# Limits: 100 requests per minute for general endpoints, 20 per minute for expensive NLQ operations
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="GIBD Quant NLQ Service",
    description="Natural language query interface for stock analysis",
    version="0.1.0"
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# SECURITY: CORS middleware with specific allowed origins
# Do not use wildcard origins with credentials
ALLOWED_ORIGINS = [
    "https://wizardsofts.com",
    "https://www.wizardsofts.com",
    "https://guardianinvestmentbd.com",
    "https://www.guardianinvestmentbd.com",
    "https://dailydeenguide.com",
    "https://www.dailydeenguide.com",
    # Development origins
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

# SECURITY: API key authentication for write operations
API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for write operations."""
    if not API_KEY:
        # If no API key configured, allow all (development mode)
        return True
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

# SECURITY: Input validation patterns
TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,10}$')  # Valid stock ticker format
QUERY_MAX_LENGTH = 500  # Maximum query length to prevent abuse

# Request/Response models with input validation
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=QUERY_MAX_LENGTH)
    tickers: Optional[List[str]] = Field(default=None, max_length=50)
    limit: Optional[int] = Field(default=50, ge=1, le=500)

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        # Strip and validate query - prevent injection attacks
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        # Block potential SQL/command injection patterns
        dangerous_patterns = ['--', ';', 'DROP', 'DELETE', 'INSERT', 'UPDATE', 'EXEC', 'EXECUTE']
        upper_v = v.upper()
        for pattern in dangerous_patterns:
            if pattern in upper_v and not any(word in upper_v for word in ['MACD', 'RSI', 'SMA', 'ADX']):
                raise ValueError('Invalid query pattern detected')
        return v

    @field_validator('tickers')
    @classmethod
    def validate_tickers(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        validated = []
        for ticker in v:
            ticker = ticker.upper().strip()
            if not TICKER_PATTERN.match(ticker):
                raise ValueError(f'Invalid ticker format: {ticker}')
            validated.append(ticker)
        return validated

class ParseRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=QUERY_MAX_LENGTH)

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Query cannot be empty')
        return v

class QueryResult(BaseModel):
    ticker: str
    value: float
    additional_info: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    query: str
    query_type: str
    results: List[QueryResult]
    total_results: int

class ParseResponse(BaseModel):
    query_type: str
    indicator: Optional[str] = None
    threshold: Optional[float] = None
    days: Optional[int] = None
    direction: Optional[str] = None
    limit: Optional[int] = None
    confidence: float

@app.get("/health")
@limiter.limit("100/minute")
async def health(request: Request):
    """Health check endpoint"""
    return {"status": "UP", "service": "gibd-quant-nlq"}

@app.post("/api/v1/nlq/query", response_model=QueryResponse)
@limiter.limit("20/minute")  # SECURITY: Rate limit expensive NLQ operations
async def execute_query(request: Request, query_request: QueryRequest):
    """Execute natural language query"""
    try:
        engine = NLQueryEngine()
        result = engine.query(
            query=query_request.query,
            tickers=query_request.tickers,
            limit=query_request.limit
        )

        return QueryResponse(
            query=query_request.query,
            query_type=result.query_type,
            results=[
                QueryResult(
                    ticker=r.get("ticker", ""),
                    value=r.get("value", 0.0),
                    additional_info={k: v for k, v in r.items() if k not in ["ticker", "value"]}
                )
                for r in result.results
            ],
            total_results=len(result.results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/nlq/parse", response_model=ParseResponse)
@limiter.limit("50/minute")  # SECURITY: Rate limit parsing operations
async def parse_query(request: Request, parse_request: ParseRequest):
    """Parse query without executing (for testing/debugging)"""
    try:
        engine = NLQueryEngine()
        parsed = engine.parse(parse_request.query)

        return ParseResponse(
            query_type=parsed.query_type,
            indicator=parsed.indicator,
            threshold=parsed.threshold,
            days=parsed.days,
            direction=parsed.direction,
            limit=parsed.limit,
            confidence=parsed.confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/nlq/examples")
@limiter.limit("100/minute")
async def get_examples(request: Request):
    """Get example queries for each supported type"""
    return {
        "examples": {
            "trend": [
                "stocks with increasing RSI for 5 days",
                "decreasing SMA_20 for 3 days",
                "stocks with rising price"
            ],
            "threshold": [
                "stocks with RSI above 70",
                "volume above average",
                "overbought stocks",
                "oversold stocks"
            ],
            "ranking": [
                "top 20 stocks by volume",
                "show 10 stocks with highest RSI",
                "stocks with lowest price",
                "show 10 Bank sector stocks with highest volume"
            ],
            "comparison": [
                "stocks outperforming their sector",
                "stocks underperforming sector"
            ],
            "crossover": [
                "MACD bullish crossover",
                "MACD bearish crossover"
            ],
            "support_resistance": [
                "price near support",
                "price near resistance"
            ]
        },
        "supported_indicators": [
            "RSI_14",
            "SMA_20",
            "SMA_50",
            "SMA_200",
            "MACD_histogram",
            "MACD_line",
            "MACD_signal",
            "ADX_14",
            "ATR_14",
            "volume",
            "price/close"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", "5002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
