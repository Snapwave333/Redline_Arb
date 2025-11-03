"""
ARBYS Backend Flask API Server

Serves real arbitrage opportunities to the mobile/web app. Complies with the
REAL_DATA_ONLY policy: no synthetic, placeholder, or mock data generation.

Endpoints:
- GET /api/health
- GET /api/opportunities?sport=soccer&min_profit_pct=1.0&limit=100&include_raw=false

Requirements: see requirements.txt (Flask, flask-cors, requests, python-dateutil)
"""

from __future__ import annotations

import os
import sys
import json
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure project root is importable when running this file directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_orchestrator import MultiAPIOrchestrator  # type: ignore
from src.arbitrage import ArbitrageDetector  # type: ignore
from src.api_providers.sofascore_scraper import (  # type: ignore
    SofaScoreScraperProvider,
)
from src.api_providers.api_sports import APISportsProvider  # type: ignore
from src.api_providers.the_odds_api import TheOddsAPIProvider  # type: ignore


app = Flask(__name__)
CORS(app)

logger = logging.getLogger("arbys.backend")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def read_version() -> str:
    """Read version string from version.txt (fallback to 'dev')."""
    try:
        version_file = os.path.join(PROJECT_ROOT, "version.txt")
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "dev"


def build_orchestrator() -> MultiAPIOrchestrator:
    """Construct the MultiAPIOrchestrator with real providers only."""
    providers = []

    # SofaScore scraper (free; uses undocumented endpoints — use responsibly)
    sofascore_enabled = os.environ.get("SOFASCORE_ENABLED", "1") not in ("0", "false", "False")
    if sofascore_enabled:
        providers.append(SofaScoreScraperProvider(enabled=True, priority=1))

    # API-Sports (free plan requires key; 100 requests/day)
    api_sports_key = os.environ.get("API_SPORTS_KEY") or os.environ.get("APISPORTS_API_KEY")
    if api_sports_key:
        providers.append(APISportsProvider(api_key=api_sports_key, enabled=True, priority=2))
    else:
        logger.info("API-Sports key not set; provider disabled")

    # The Odds API (paid; optional)
    the_odds_key = os.environ.get("THE_ODDS_API_KEY") or os.environ.get("ODDS_API_KEY")
    if the_odds_key:
        providers.append(TheOddsAPIProvider(api_key=the_odds_key, enabled=True, priority=3))
    else:
        logger.info("The Odds API key not set; provider disabled")

    orchestrator = MultiAPIOrchestrator(
        providers=providers,
        failover_enabled=True,
        require_all_providers=False,
    )
    return orchestrator


ORCHESTRATOR = build_orchestrator()


@app.get("/api/health")
def api_health():
    """Return backend health and provider status."""
    try:
        provider_status = ORCHESTRATOR.get_provider_status()
        # Convert ProviderHealth dataclasses to dicts
        provider_status_dict = {name: asdict(health) for name, health in provider_status.items()}

        return jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": read_version(),
                "server": "arbys-backend",
                "providers": provider_status_dict,
            }
        )
    except Exception as e:
        logger.exception("Health endpoint error: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500


@app.get("/api/opportunities")
def api_opportunities():
    """
    Return real arbitrage opportunities computed from provider odds.

    Query params:
    - sport: string (default 'soccer')
    - min_profit_pct: float (default 1.0)
    - limit: int (default 100)
    - include_raw: bool (default false) include per-provider normalized raw for validation
    """
    try:
        sport = request.args.get("sport", "soccer").strip()
        # REAL_DATA_ONLY policy enforced implicitly by not generating synthetic data
        min_profit_pct = float(request.args.get("min_profit_pct", "1.0"))
        try:
            limit = int(request.args.get("limit", "100"))
            limit = max(1, min(limit, 500))  # cap to 500 for safety
        except Exception:
            limit = 100
        include_raw = request.args.get("include_raw", "false").lower() in ("1", "true", "yes")

        # Fetch odds from orchestrator (real providers only)
        merged_events, errors, latency = ORCHESTRATOR.fetch_odds(sport)

        # Compute arbitrage opportunities
        detector = ArbitrageDetector(min_profit_percentage=min_profit_pct)
        arbs = detector.find_best_arbitrages(merged_events)

        # Prepare response schema compatible with mobile_web_app/src/services/api.ts
        opportunities = []
        for idx, arb in enumerate(arbs[:limit]):
            # Flatten ArbitrageOpportunity to dict
            opp = {
                "id": f"{sport}-{int(datetime.now().timestamp())}-{idx}",
                "event_name": arb.event_name,
                "market": arb.market,
                "outcomes": [],
                "total_implied_probability": arb.total_implied_probability,
                "profit_percentage": arb.profit_percentage,
                "bookmakers": arb.bookmakers,
                "timestamp": arb.timestamp,
                "risk_level": arb.risk_level,
                "risk_warnings": arb.risk_warnings,
                "sport": sport,
                "commence_time": None,
            }

            # Preserve commence_time if available in source_raw by peeking one provider
            # The detector copies event_context including 'commence_time' into source_raw if provided
            # but we also try to read it from merged event contexts when present
            try:
                # Extract commence_time from source_raw first match
                if include_raw and arb.source_raw:
                    for _prov, ev in arb.source_raw.items():
                        ct = ev.get("commence_time")
                        if ct:
                            opp["commence_time"] = ct
                            break
                # Fallback: None; UI handles missing commence_time gracefully
            except Exception:
                pass

            # Outcomes with explicit odds_format
            for outcome in arb.outcomes:
                opp["outcomes"].append(
                    {
                        "outcome_name": outcome.get("outcome_name"),
                        "odds": float(outcome.get("odds", 0)),
                        "original_odds": outcome.get("original_odds", outcome.get("odds")),
                        "original_format": outcome.get("original_format", "decimal"),
                        "bookmaker": outcome.get("bookmaker", "Unknown"),
                        "odds_format": "decimal",
                    }
                )

            # Provide nested arbitrage_opportunity for frontend compatibility
            opp["arbitrage_opportunity"] = {
                "profit_percentage": arb.profit_percentage,
                "total_implied_probability": arb.total_implied_probability,
                "risk_level": arb.risk_level,
                "risk_warnings": arb.risk_warnings,
                "source_apis": arb.source_apis,
            }

            if include_raw:
                opp["source_raw"] = arb.source_raw or {}

            opportunities.append(opp)

        resp = {
            "count": len(opportunities),
            "sport": sport,
            "min_profit_pct": min_profit_pct,
            "latency": latency,
            "errors": errors,
            "opportunities": opportunities,
        }

        return jsonify(resp)

    except Exception as e:
        logger.exception("Opportunities endpoint error: %s", e)
        return jsonify({"error": str(e)}), 500


def run():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("DEBUG", "0") in ("1", "true", "True")
    logger.info(f"Starting ARBYS backend server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run()