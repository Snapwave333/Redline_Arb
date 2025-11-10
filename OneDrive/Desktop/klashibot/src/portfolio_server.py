#!/usr/bin/env python3
"""
Simple portfolio server to show real Kalshi account data in dashboard
Adds trades stream endpoints to feed the Live Trades panel.
"""

import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body
from pydantic import BaseModel
import sys
from pathlib import Path
from src.firebase_manager import FirebaseManager
from src.config import config

# Fix imports - go to parent directory
src_dir = Path(__file__).parent
parent_dir = src_dir.parent
sys.path.insert(0, str(parent_dir))

# Import after fixing path
from src.kalshi_client import KalshiAPIClient
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = None
firebase_manager: FirebaseManager | None = None

# In-memory trades buffer for lightweight streaming
MAX_TRADES = 500
trades_buffer: List[Dict[str, Any]] = []

class Trade(BaseModel):
    timestamp: str
    order_id: str
    direction: str
    ticker: str
    shares: int
    price: float
    pnl: float = 0.0
    status: str = "submitted"

@app.on_event("startup")
async def startup():
    global client, firebase_manager
    try:
        client = KalshiAPIClient()
        await client.__aenter__()
        print("✅ Connected to Kalshi API")
    except Exception as e:
        print(f"⚠️ Could not connect to Kalshi: {e}")
        client = None
    # Initialize Firebase optionally
    try:
        if config.firebase.firebase_enabled:
            firebase_manager = FirebaseManager(
                app_id=config.firebase.firebase_app_id,
                user_id=config.firebase.firebase_user_id,
                region=config.firebase.firebase_region,
            )
            firebase_manager.initialize(
                config.firebase.firebase_credentials_path,
                config.firebase.firebase_database_id,
            )
            print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase init failed: {e}")
        firebase_manager = None

@app.get("/portfolio")
async def get_portfolio():
    """Get real portfolio from Kalshi account"""
    if not client:
        return {"success": False, "error": "Client not initialized"}
    try:
        portfolio = await client.get_portfolio()
        return {"success": True, "data": portfolio}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/positions")
async def get_positions():
    """Get real positions"""
    if not client:
        return {"success": False, "error": "Client not initialized"}
    try:
        positions = await client.get_positions()
        return {"success": True, "data": positions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/positions/combined")
async def get_positions_combined(refresh: bool = False):
    """Combine positions from Kalshi API and Firebase storage"""
    try:
        kalshi_positions = await client.get_positions() if client else []
        fb_positions = []
        if firebase_manager:
            fb_positions = firebase_manager.get_positions() or []
        # Simple merge by ticker
        merged: dict[str, dict] = {}
        for p in kalshi_positions:
            merged[p.ticker] = {
                "ticker": p.ticker,
                "side": getattr(p, "side", "unknown"),
                "quantity": getattr(p, "quantity", 0),
                "average_price": getattr(p, "average_price", 0.0),
                "source": ["kalshi"],
            }
        for fp in fb_positions:
            t = fp.get("ticker") or fp.get("marketId") or fp.get("id")
            if not t:
                continue
            if t in merged:
                merged[t]["quantity"] = int(merged[t]["quantity"]) + int(fp.get("quantity", 0))
                merged[t]["source"].append("firebase")
            else:
                merged[t] = {
                    "ticker": t,
                    "side": fp.get("side", "unknown"),
                    "quantity": int(fp.get("quantity", 0)),
                    "average_price": float(fp.get("averagePrice", fp.get("price", 0.0))),
                    "source": ["firebase"],
                }
        return {
            "success": True,
            "kalshi": [p.__dict__ for p in kalshi_positions],
            "firebase": fb_positions,
            "merged": list(merged.values()),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/balance")
async def get_balance():
    """Get account balance"""
    if not client:
        return {"success": False, "error": "Client not initialized"}
    try:
        portfolio = await client.get_portfolio()
        balance = portfolio.get("balance", 0) if portfolio else 0
        return {"success": True, "balance": balance}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.websocket("/ws/portfolio")
async def ws_portfolio(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                if client:
                    portfolio = await client.get_portfolio()
                else:
                    portfolio = {"total_value": 0, "cash_balance": 0}
                await websocket.send_json({"success": True, "data": portfolio})
            except Exception as e:
                await websocket.send_json({"success": False, "error": str(e)})
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        # Client disconnected
        return

# Trades Stream Endpoints
@app.post("/trades/push")
async def push_trade(trade: Trade):
    """Push a trade from the bot into the in-memory stream buffer"""
    try:
        trade_dict = trade.dict()
        trades_buffer.insert(0, trade_dict)
        if len(trades_buffer) > MAX_TRADES:
            trades_buffer.pop()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/trades/latest")
async def get_latest_trade():
    """Return the latest trade for the LiveTradesTerminal"""
    try:
        if trades_buffer:
            return {"success": True, "trade": trades_buffer[0]}
        return {"success": True, "trade": None}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)

