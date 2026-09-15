---
type: "query"
date: "2026-09-06T08:15:58.321454+00:00"
question: "what equity or single stock elements are in the code base?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["StockstatsUtils", "AssetType", "get_balance_sheet()", "create_fundamentals_analyst()", "build_instrument_context()", "test_equity_mode_unchanged()", "TradingAgentsGraph"]
---

# Q: what equity or single stock elements are in the code base?

## Answer

Expanded from original query via vocab: [equity, stock, single, ticker, stockstats, stocktwits, fundamentals, financials, asset, balance, market, shares]. Traversed graph and identified equity-mode agents (Bull/Bear researchers, Fundamentals Analyst, Research Manager, Trader, Portfolio Manager), dataflows (yfinance balance sheet, income statement, Stockstats technical indicators, Alpha Vantage stock/fundamentals, insider transactions), instrument resolution (company name, sector, exchange from yfinance), AssetType enum (STOCK vs CRYPTO), and dual-track graph execution where non-FI analysts route to the equity pipeline.

## Outcome

- Signal: useful

## Source Nodes

- StockstatsUtils
- AssetType
- get_balance_sheet()
- create_fundamentals_analyst()
- build_instrument_context()
- test_equity_mode_unchanged()
- TradingAgentsGraph