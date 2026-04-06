"""
GoldTrader AI Agent — FastAPI Gateway
Entry point for the API layer. CORS enabled for dashboard.
Reference: ARCHITECTURE.md Section 6
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from agent.config import load_config
from agent.database import Database
from api.state import AgentState
from api.routes import agent, trades, analytics, stream

# Load config and connect to same DB as agent
config = load_config()
db = Database(config.db_full_path)

# Create shared state
agent_state = AgentState(db)

# FastAPI app
app = FastAPI(
    title="GoldTrader AI Agent API",
    description="Real-time monitoring and control for the XAUUSD trading agent",
    version="1.0.0",
)

# CORS — allow dashboard (localhost:5173 by default for Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach shared state to app
app.state.agent_state = agent_state

# Mount routes
app.include_router(agent.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(stream.router, prefix="/api")


@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "GoldTrader AI Agent API",
        "status": "running",
        "docs": "/docs",
    }


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    db.close()


def start():
    """Entry point for running the API server."""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    start()
