"""
data_fetchers/fetcher.py
Unified data fetcher: yfinance (free) + FMP (premium) + scraping fallbacks
Covers: PSX, NSE, BSE, NYSE, NASDAQ, LSE, TADAWUL, DFM, ADX, etc.
"""

import os
import time
import json
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import streamlit as st

# ─── CONFIG ──────────────────────────────────────────────────────────────────
def _get_key(name):
    """Get API key from Streamlit secrets or environment."""
    try:
        return st.secrets["api_keys"].get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")

FMP_BASE = "https://financialmodelingprep.com/api/v3"
AV_BASE  = "https://www.alphavantage.co/query"

# Exchange → Yahoo Finance suffix mapping
EXCHANGE_SUFFIX = {
    "PSX":     ".KA",     # Pakistan Stock Exchange (Karachi)
    "NSE":     ".NS",     # India National Stock Exchange
    "BSE":     ".BO",     # India Bombay Stock Exchange
    "TADAWUL": ".SR",     # Saudi Arabia (Tadawul)
    "DFM":     ".DU",     # Dubai Financial Market
    "ADX":     ".AD",     # Abu Dhabi Securities Exchange
    "EGX":     ".CA",     # Egypt Exchange
    "LSE":     ".L",      # London Stock Exchange
    "TSX":     ".TO",     # Toronto Stock Exchange
    "ASX":     ".AX",     # Australian Securities Exchange
    "SGX":     ".SI",     # Singapore Exchange
    "HKEX":    ".HK",     # Hong Kong Exchange
    "SSE":     ".SS",     # Shanghai Stock Exchange
    "SZSE":    ".SZ",     # Shenzhen Stock Exchange
    "TSE":     ".T",      # Tokyo Stock Exchange
    "KRX":     ".KS",     # Korea Stock Exchange
    "NYSE":    "",         # US (no suffix)
    "NASDAQ":  "",         # US (no suffix)
    "SP500":   "",         # US (no suffix)
}

POPULAR_EXCHANGES = {
    "🇵🇰 Pakistan (PSX)": "PSX",
    "🇸🇦 Saudi Arabia (Tadawul)": "TADAWUL",
    "🇦🇪 UAE (DFM)": "DFM",
    "🇦🇪 UAE (ADX)": "ADX",
    "🇮🇳 India (NSE)": "NSE",
    "🇮🇳 India (BSE)": "BSE",
    "🇪🇬 Egypt (EGX)": "EGX",
    "🇺🇸 USA (NYSE/NASDAQ)": "NYSE",
    "🇬🇧 UK (LSE)": "LSE",
    "🇦🇺 Australia (ASX)": "ASX",
    "🇸🇬 Singapore (SGX)": "SGX",
    "🇭🇰 Hong Kong (HKEX)": "HKEX",
    "🇯🇵 Japan (TSE)": "TSE",
    "🇰🇷 Korea (KRX)": "KRX",
    "🇨🇦 Canada (TSX)": "TSX",
}

# ─── MAIN FETCHER CLASS ───────────────────────────────────────────────────────
class DataFetcher:
    def __init__(self):
        self.fmp_key   = _get_key("FMP_API_KEY")
        self.av_key    = _get_key("ALPHA_VANTAGE_API_KEY")
        self._cache    = {}

    def _cache_get(self, key):
        item = self._cache.get(key)
        if item and time.time() - item["ts"] < 3600:
            return item["data"]
        return None

    def _cache_set(self, key, data):
        self._cache[key] = {"data": data, "ts": time.time()}

    def build_ticker(self, ticker: str, exchange: str) -> str:
        """Append Yahoo Finance exchange suffix."""
        suffix = EXCHANGE_SUFFIX.get(exchange, "")
        t = ticker.upper().strip()
        if suffix and not t.endswith(suffix):
            return t + suffix
        return t

    # ── SEARCH ───────────────────────────────────────────────────────────────
    def search_companies(self, query: str, exchange: str = None) -> list[dict]:
        """Search listed companies by name or ticker."""
        results = []
        # Try FMP search first
        if self.fmp_key:
            try:
                url = f"{FMP_BASE}/search?query={query}&limit=20&apikey={self.fmp_key}"
                r = requests.get(url, timeout=10)
                data = r.json()
                for item in data:
                    exch = item.get("exchangeShortName", "")
                    if exchange and exchange not in ["NYSE", "NASDAQ"] and exch not in [exchange, ""]:
                        continue
                    results.append({
                        "ticker": item.get("symbol", ""),
                        "name": item.get("name", ""),
                        "exchange": exch,
                        "currency": item.get("currency", "USD"),
                        "country": item.get("stockExchange", ""),
                    })
                return results[:15]
            except Exception:
                pass

        # Fallback: yfinance search
        try:
            suffix = EXCHANGE_SUFFIX.get(exchange, "") if exchange else ""
            yt = yf.Ticker(query + suffix)
            info = yt.info
            if info.get("longName"):
                results.append({
                    "ticker": query + suffix,
                    "name": info.get("longName", query),
                    "exchange": info.get("exchange", exchange or ""),
                    "currency": info.get("currency", "USD"),
                    "country": info.get("country", ""),
                })
        except Exception:
            pass
        return results

    def _fetch_yfinance(_self, ticker: str, exchange: str):
        candidates = []
        clean_ticker = ticker.upper().strip()

        if exchange in ["NYSE", "NASDAQ", "SP500"]:
            candidates.append(clean_ticker)
        else:
            suffix = EXCHANGE_SUFFIX.get(exchange, "")
            if suffix and not clean_ticker.endswith(suffix):
                candidates.append(clean_ticker + suffix)
            candidates.append(clean_ticker)

        last_err = None
        for yt in candidates:
            try:
                stock = yf.Ticker(yt)
                info = stock.info
                
                # If .info is empty, try to get data from history as validation
                if not info or (not info.get("longName") and not info.get("regularMarketPrice") and not info.get("shortName")):
                    # Try to fetch history as fallback validation
                    hist = stock.history(period="1d")
                    if hist.empty:
                        raise ValueError(f"No valid data from Yahoo Finance for ticker {yt}")
                    # If history exists, info dict might be loading, retry once more
                    info = stock.info or {}
                    if not info.get("longName") and not info.get("shortName"):
                        info["longName"] = yt
                        info["shortName"] = yt
                
                return yt, stock, info
            except Exception as e:
                last_err = e
                continue

        raise ValueError(f"Yahoo Finance fetch failed for {ticker} ({exchange}), tried: {candidates}. Last error: {last_err}")

    # ── CORE FINANCIAL DATA ───────────────────────────────────────────────────
    @st.cache_data(ttl=3600, show_spinner=False)
    def fetch_company_data(_self, ticker: str, exchange: str, years: int = 5) -> dict:
        """Fetch complete company financial data."""
        cache_key = f"{ticker}_{exchange}_{years}"
        cached = _self._cache_get(cache_key)
        if cached:
            return cached

        # Try FMP first if key is configured
        if _self.fmp_key:
            fmp_result = _self._fetch_fmp(ticker, exchange, years, {"ticker": ticker, "exchange": exchange, "source": "fmp"})
            if fmp_result.get("success"):
                _self._cache_set(cache_key, fmp_result)
                return fmp_result
            fmp_error = fmp_result.get("error")
        else:
            fmp_error = "FMP API key not provided"

        result = {"ticker": ticker, "exchange": exchange, "source": "yfinance"}

        # Try yfinance with fallback tickers
        try:
            yt, stock, info = _self._fetch_yfinance(ticker, exchange)
            result.update({"yf_ticker": yt, "source": "yfinance"})

            # Company profile
            result["profile"] = {
                "name":         info.get("longName", info.get("shortName", ticker)),
                "sector":       info.get("sector", "Unknown"),
                "industry":     info.get("industry", "Unknown"),
                "country":      info.get("country", ""),
                "currency":     info.get("currency", "USD"),
                "website":      info.get("website", ""),
                "description":  info.get("longBusinessSummary", ""),
                "employees":    info.get("fullTimeEmployees", 0),
                "market_cap":   info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "share_price":  info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "shares_out":   info.get("sharesOutstanding", 0),
                "beta":         info.get("beta", 1.0),
                "52w_high":     info.get("fiftyTwoWeekHigh", 0),
                "52w_low":      info.get("fiftyTwoWeekLow", 0),
                "pe":           info.get("trailingPE", 0),
                "forward_pe":   info.get("forwardPE", 0),
                "pb":           info.get("priceToBook", 0),
                "ev_ebitda":    info.get("enterpriseToEbitda", 0),
                "ev_revenue":   info.get("enterpriseToRevenue", 0),
                "div_yield":    (info.get("dividendYield", 0) or 0) * 100,
                "roe":          info.get("returnOnEquity", 0),
                "roa":          info.get("returnOnAssets", 0),
                "profit_margin":info.get("profitMargins", 0),
                "gross_margin": info.get("grossMargins", 0),
                "ebitda_margin":info.get("ebitdaMargins", 0),
                "op_margin":    info.get("operatingMargins", 0),
                "revenue_growth":info.get("revenueGrowth", 0),
                "earnings_growth":info.get("earningsGrowth", 0),
                "debt_to_equity":info.get("debtToEquity", 0),
                "current_ratio":info.get("currentRatio", 0),
                "quick_ratio":  info.get("quickRatio", 0),
                "fcf":          info.get("freeCashflow", 0),
                "operating_cf": info.get("operatingCashflow", 0),
            }

            # Income Statement (annual)
            inc = stock.financials.T if not stock.financials.empty else pd.DataFrame()
            bal = stock.balance_sheet.T if not stock.balance_sheet.empty else pd.DataFrame()
            csh = stock.cashflow.T if not stock.cashflow.empty else pd.DataFrame()

            result["income"]        = _self._parse_income(inc, years)
            result["balance_sheet"] = _self._parse_balance(bal, years)
            result["cashflow"]      = _self._parse_cashflow(csh, years)
            result["kpis"]          = _self._calc_kpis(result)
            result["market_data"]   = _self._fetch_market_data(stock, info)
            result["success"]       = True

        except Exception as e:
            yf_error = str(e)
            result["error"] = f"yfinance: {yf_error}"
            result["success"] = False

        # Try FMP as supplement / override if key available
        if not result.get("success") and _self.fmp_key:
            fmp_result = _self._fetch_fmp(ticker, exchange, years, {"ticker": ticker, "exchange": exchange, "source": "fmp"})
            if fmp_result.get("success"):
                _self._cache_set(cache_key, fmp_result)
                return fmp_result
            result["error"] = f"yfinance: {yf_error}; fmp: {fmp_result.get('error', 'unknown')}"
            result["success"] = False

        if not result.get("success") and not result.get("error"):
            result["error"] = "Unable to fetch data from yfinance and FMP. Please check ticker and API keys."

        _self._cache_set(cache_key, result)
        return result

    def _parse_income(self, df: pd.DataFrame, years: int) -> list[dict]:
        rows = []
        if df.empty:
            return rows
        df = df.head(years)
        for idx, row in df.iterrows():
            try:
                year = pd.to_datetime(idx).year
            except Exception:
                year = idx
            revenue        = _safe(row, ["Total Revenue", "Revenue"])
            cogs           = _safe(row, ["Cost Of Revenue", "Cost of Revenue"])
            gross_profit   = _safe(row, ["Gross Profit"]) or (revenue - cogs if revenue and cogs else 0)
            ebit           = _safe(row, ["Operating Income", "EBIT"])
            dep            = _safe(row, ["Depreciation", "Depreciation & Amortization", "Reconciled Depreciation"])
            ebitda         = (ebit or 0) + (dep or 0)
            ni             = _safe(row, ["Net Income", "Net Income Common Stockholders"])
            interest       = abs(_safe(row, ["Interest Expense", "Interest Expense Non Operating"]) or 0)
            tax            = abs(_safe(row, ["Tax Provision", "Income Tax Expense"]) or 0)
            rows.append({
                "year": year, "revenue": revenue or 0, "cogs": cogs or 0,
                "gross_profit": gross_profit or 0, "ebitda": ebitda or 0,
                "ebit": ebit or 0, "net_income": ni or 0,
                "interest_expense": interest, "tax_expense": tax, "depreciation": dep or 0,
            })
        return sorted(rows, key=lambda x: x["year"])

    def _parse_balance(self, df: pd.DataFrame, years: int) -> list[dict]:
        rows = []
        if df.empty:
            return rows
        df = df.head(years)
        for idx, row in df.iterrows():
            try:
                year = pd.to_datetime(idx).year
            except Exception:
                year = idx
            total_assets      = _safe(row, ["Total Assets"])
            total_equity      = _safe(row, ["Stockholders Equity", "Total Stockholders Equity", "Common Stock Equity"])
            total_debt        = _safe(row, ["Total Debt", "Long Term Debt And Capital Lease Obligation"])
            ltd               = _safe(row, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"])
            std               = _safe(row, ["Short Term Debt", "Current Debt", "Current Portion Of Long Term Debt And Capital Lease Obligations"])
            cash              = _safe(row, ["Cash And Cash Equivalents", "Cash Financial"])
            current_assets    = _safe(row, ["Current Assets"])
            current_liabilities = _safe(row, ["Current Liabilities"])
            inventory         = _safe(row, ["Inventory"])
            receivables       = _safe(row, ["Accounts Receivable", "Net Accounts Receivable", "Receivables"])
            payables          = _safe(row, ["Accounts Payable"])
            rows.append({
                "year": year,
                "total_assets": total_assets or 0,
                "total_equity": total_equity or 0,
                "debt": total_debt or (ltd or 0) + (std or 0),
                "long_term_debt": ltd or 0,
                "cash": cash or 0,
                "current_assets": current_assets or 0,
                "current_liabilities": current_liabilities or 0,
                "inventory": inventory or 0,
                "receivables": receivables or 0,
                "payables": payables or 0,
            })
        return sorted(rows, key=lambda x: x["year"])

    def _parse_cashflow(self, df: pd.DataFrame, years: int) -> list[dict]:
        rows = []
        if df.empty:
            return rows
        df = df.head(years)
        for idx, row in df.iterrows():
            try:
                year = pd.to_datetime(idx).year
            except Exception:
                year = idx
            cfo   = _safe(row, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
            capex = abs(_safe(row, ["Capital Expenditure", "Capital Expenditures", "Purchase Of PPE"]) or 0)
            fcf   = (cfo or 0) - capex
            rows.append({"year": year, "cfo": cfo or 0, "capex": capex, "fcf": fcf})
        return sorted(rows, key=lambda x: x["year"])

    def _calc_kpis(self, data: dict) -> list[dict]:
        """Calculate full KPI set from parsed financials."""
        inc = {r["year"]: r for r in data.get("income", [])}
        bal = {r["year"]: r for r in data.get("balance_sheet", [])}
        cf  = {r["year"]: r for r in data.get("cashflow", [])}
        years = sorted(set(inc) & set(bal) & set(cf))
        kpis = []
        prev_year = None
        for yr in years:
            f = inc[yr]; b = bal[yr]; c = cf[yr]
            prev_f = inc.get(prev_year)
            prev_b = bal.get(prev_year)
            rev   = f["revenue"] or 1
            ebitda = f["ebitda"] or 0
            ebit   = f["ebit"] or 0
            ni     = f["net_income"] or 0
            eq     = b["total_equity"] or 1
            assets = b["total_assets"] or 1
            debt   = b["debt"] or 0
            cash   = b["cash"] or 0
            cfo    = c["cfo"]
            fcf    = c["fcf"]
            capex  = c["capex"]
            cogs   = f["cogs"] or rev * 0.6
            inv    = b["inventory"] or 0
            rec    = b["receivables"] or 0
            pay    = b["payables"] or 0
            curr_a = b["current_assets"] or 0
            curr_l = b["current_liabilities"] or 1
            tax_rate = 0.28
            nopat  = ebit * (1 - tax_rate)
            inv_cap = max(debt + eq - cash, 1)
            kpi = {
                "year": yr,
                "revenue": rev,
                "ebitda": ebitda,
                "net_income": ni,
                "gross_margin":   f["gross_profit"] / rev,
                "ebitda_margin":  ebitda / rev,
                "ebit_margin":    ebit / rev,
                "net_margin":     ni / rev,
                "roe":    ni / ((eq + (prev_b["total_equity"] if prev_b else eq)) / 2) if prev_b else ni / eq,
                "roa":    ni / ((assets + (prev_b["total_assets"] if prev_b else assets)) / 2) if prev_b else ni / assets,
                "roic":   nopat / inv_cap,
                "revenue_growth": (rev - prev_f["revenue"]) / max(prev_f["revenue"], 1) if prev_f else None,
                "ebitda_growth":  (ebitda - prev_f["ebitda"]) / max(abs(prev_f["ebitda"]), 1) if prev_f else None,
                "ni_growth":      (ni - prev_f["net_income"]) / max(abs(prev_f["net_income"]), 1) if prev_f else None,
                "cfo": cfo, "capex": capex, "fcf": fcf,
                "cfo_margin":    cfo / rev,
                "fcf_margin":    fcf / rev,
                "cfo_to_ni":     cfo / max(abs(ni), 1),
                "capex_intensity": capex / rev,
                "debt_equity":   debt / max(eq, 1),
                "debt_ebitda":   debt / max(abs(ebitda), 1),
                "net_debt":      debt - cash,
                "net_debt_ebitda": (debt - cash) / max(abs(ebitda), 1),
                "interest_coverage": ebit / max(f["interest_expense"], 1),
                "current_ratio": curr_a / curr_l,
                "quick_ratio":   (curr_a - inv) / curr_l,
                "cash_ratio":    cash / curr_l,
                "asset_turnover":  rev / max(assets, 1),
                "inventory_days":  (inv / max(cogs, 1)) * 365,
                "receivable_days": (rec / max(rev, 1)) * 365,
                "payable_days":    (pay / max(cogs, 1)) * 365,
            }
            kpi["ccc"] = kpi["inventory_days"] + kpi["receivable_days"] - kpi["payable_days"]
            kpis.append(kpi)
            prev_year = yr
        return kpis

    def _fetch_market_data(self, stock, info: dict) -> dict:
        return {
            "share_price":  info.get("currentPrice", 0),
            "market_cap":   info.get("marketCap", 0),
            "ev":           info.get("enterpriseValue", 0),
            "pe":           info.get("trailingPE", 0) or 0,
            "forward_pe":   info.get("forwardPE", 0) or 0,
            "pb":           info.get("priceToBook", 0) or 0,
            "ev_ebitda":    info.get("enterpriseToEbitda", 0) or 0,
            "ev_revenue":   info.get("enterpriseToRevenue", 0) or 0,
            "div_yield":    (info.get("dividendYield", 0) or 0) * 100,
            "beta":         info.get("beta", 1.0) or 1.0,
            "52w_high":     info.get("fiftyTwoWeekHigh", 0),
            "52w_low":      info.get("fiftyTwoWeekLow", 0),
            "analyst_target": info.get("targetMeanPrice", 0),
            "recommendation": info.get("recommendationKey", "hold"),
        }

    def _fetch_fmp(self, ticker: str, exchange: str, years: int, fallback: dict) -> dict:
        """Supplement with FMP data if available."""
        try:
            # For US stocks, use plain ticker; for others, try with suffix
            fmp_tickers = [ticker.upper().strip()]
            if exchange not in ["NYSE", "NASDAQ", "SP500"]:
                suffix = EXCHANGE_SUFFIX.get(exchange, "")
                if suffix:
                    fmp_tickers.insert(0, ticker.upper().strip() + suffix)
            
            profile_data = None
            fmp_ticker_used = None
            
            # Try each ticker format
            for fmp_ticker in fmp_tickers:
                try:
                    profile_url = f"{FMP_BASE}/profile/{fmp_ticker}?apikey={self.fmp_key}"
                    r = requests.get(profile_url, timeout=10)
                    if r.status_code != 200:
                        continue
                    try:
                        profiles = r.json()
                    except ValueError:
                        continue
                    
                    if profiles and isinstance(profiles, list) and len(profiles) > 0:
                        profile_data = profiles[0]
                        fmp_ticker_used = fmp_ticker
                        break
                except Exception:
                    continue
            
            if not profile_data:
                fallback["error"] = f"FMP profile unavailable for {ticker} (tried: {fmp_tickers})"
                fallback["success"] = False
                return fallback

            fallback["profile"] = fallback.get("profile", {})
            fallback["profile"].update({
                "name": profile_data.get("companyName", ticker),
                "sector": profile_data.get("sector", "Unknown"),
                "industry": profile_data.get("industry", "Unknown"),
                "country": profile_data.get("country", ""),
                "currency": profile_data.get("currency", "USD"),
                "description": profile_data.get("description", ""),
                "market_cap": profile_data.get("mktCap", 0),
                "share_price": profile_data.get("price", 0),
                "beta": profile_data.get("beta", 1.0),
            })

            def get_statement(stmt_name):
                try:
                    url = f"{FMP_BASE}/{stmt_name}/{fmp_ticker_used}?period=annual&limit={years}&apikey={self.fmp_key}"
                    rr = requests.get(url, timeout=10)
                    if rr.status_code != 200:
                        return []
                    data = rr.json()
                    return data if isinstance(data, list) else []
                except Exception:
                    return []

            income_raw = get_statement("income-statement")
            balance_raw = get_statement("balance-sheet-statement")
            cashflow_raw = get_statement("cash-flow-statement")

            def map_income(row):
                return {
                    "year": int(str(row.get("calendarYear", "0"))[:4]) if row.get("calendarYear") else None,
                    "revenue": row.get("revenue", 0),
                    "cogs": row.get("costOfRevenue", 0),
                    "gross_profit": row.get("grossProfit", 0),
                    "ebitda": row.get("ebitda", 0),
                    "ebit": row.get("ebit", 0),
                    "net_income": row.get("netIncome", 0),
                    "interest_expense": abs(row.get("interestExpense", 0) or 0),
                    "tax_expense": abs(row.get("incomeTaxExpense", 0) or 0),
                    "depreciation": row.get("depreciationAndAmortization", 0),
                }

            def map_balance(row):
                debt = row.get("totalDebt", 0) or (row.get("longTermDebt", 0) or 0) + (row.get("shortTermDebt", 0) or 0)
                return {
                    "year": int(str(row.get("calendarYear", "0"))[:4]) if row.get("calendarYear") else None,
                    "total_assets": row.get("totalAssets", 0),
                    "total_equity": row.get("totalStockholdersEquity", 0),
                    "debt": debt,
                    "long_term_debt": row.get("longTermDebt", 0),
                    "cash": row.get("cashAndCashEquivalents", 0),
                    "current_assets": row.get("totalCurrentAssets", 0),
                    "current_liabilities": row.get("totalCurrentLiabilities", 1),
                    "inventory": row.get("inventory", 0),
                    "receivables": row.get("netReceivables", 0),
                    "payables": row.get("accountsPayable", 0),
                }

            def map_cashflow(row):
                return {
                    "year": int(str(row.get("calendarYear", "0"))[:4]) if row.get("calendarYear") else None,
                    "cfo": row.get("netCashProvidedByOperatingActivities", 0),
                    "capex": abs(row.get("capitalExpenditures", 0) or 0),
                    "fcf": row.get("freeCashFlow", 0),
                }

            fallback["income"] = [map_income(x) for x in income_raw if x.get("calendarYear")][:years]
            fallback["balance_sheet"] = [map_balance(x) for x in balance_raw if x.get("calendarYear")][:years]
            fallback["cashflow"] = [map_cashflow(x) for x in cashflow_raw if x.get("calendarYear")][:years]

            if fallback["income"] and fallback["balance_sheet"] and fallback["cashflow"]:
                fallback["kpis"] = self._calc_kpis(fallback)
                fallback["market_data"] = {
                    "share_price": fallback["profile"].get("share_price", 0),
                    "market_cap": fallback["profile"].get("market_cap", 0),
                    "pe": fallback["profile"].get("pe", 0),
                    "pb": fallback["profile"].get("pb", 0),
                }
                fallback["success"] = True
            else:
                fallback["success"] = False
                fallback["error"] = fallback.get("error", "Incomplete FMP financials")

        except Exception as ex:
            fallback["error"] = f"FMP fallback failed: {ex}"
            fallback["success"] = False

        return fallback

    # ── MACRO DATA ────────────────────────────────────────────────────────────
    def fetch_macro_data(self, country: str) -> dict:
        """Fetch macro indicators for a country using World Bank API."""
        country_codes = {
            "Pakistan": "PK", "Saudi Arabia": "SA", "UAE": "AE",
            "India": "IN", "USA": "US", "UK": "GB", "Egypt": "EG",
            "Australia": "AU", "Singapore": "SG", "Hong Kong": "HK",
            "Japan": "JP", "South Korea": "KR", "Canada": "CA",
        }
        code = country_codes.get(country, "US")
        indicators = {
            "gdp_growth":    "NY.GDP.MKTP.KD.ZG",
            "inflation":     "FP.CPI.TOTL.ZG",
            "unemployment":  "SL.UEM.TOTL.ZS",
            "current_acc":   "BN.CAB.XOKA.GD.ZS",
            "public_debt":   "GC.DOD.TOTL.GD.ZS",
            "interest_rate": "FR.INR.LEND",
        }
        macro = {"country": country, "code": code}
        for key, ind_code in indicators.items():
            try:
                url = f"https://api.worldbank.org/v2/country/{code}/indicator/{ind_code}?format=json&mrv=5&per_page=5"
                r = requests.get(url, timeout=8)
                data = r.json()
                if len(data) > 1 and data[1]:
                    vals = [d["value"] for d in data[1] if d["value"] is not None]
                    macro[key] = vals[0] if vals else None
                    macro[f"{key}_history"] = vals
            except Exception:
                macro[key] = None
        return macro

    # ── PRIVATE COMPANY ───────────────────────────────────────────────────────
    def parse_uploaded_financials(self, df: pd.DataFrame, sheet_name: str = "") -> dict:
        """Parse user-uploaded Excel/CSV financial data."""
        result = {"source": "upload", "success": False, "income": [], "balance_sheet": [], "cashflow": []}
        try:
            df.columns = [str(c).strip().lower() for c in df.columns]
            years = [c for c in df.columns if str(c).isdigit() or (len(str(c)) == 4 and str(c)[:2] in ["19", "20"])]
            if not years:
                cols_num = [c for c in df.columns if c not in ["metric", "item", "description", "account"]]
                years = cols_num[:5]

            row_map = {str(r).strip().lower(): i for i, r in enumerate(df.iloc[:, 0]) if pd.notna(r)}
            def get_row(keywords):
                for kw in keywords:
                    for key, idx in row_map.items():
                        if kw.lower() in key:
                            return df.iloc[idx]
                return None

            for yr in years:
                def v(keywords):
                    row = get_row(keywords)
                    if row is None:
                        return 0
                    try:
                        val = row[yr]
                        return float(str(val).replace(",", "").replace("(", "-").replace(")", "")) if pd.notna(val) else 0
                    except Exception:
                        return 0

                revenue    = v(["revenue", "sales", "turnover", "net sales"])
                cogs       = v(["cost of revenue", "cost of goods", "cogs", "cost of sales"])
                gp         = v(["gross profit"]) or (revenue - cogs)
                ebitda     = v(["ebitda"])
                ebit       = v(["ebit", "operating income", "operating profit"])
                ni         = v(["net income", "net profit", "profit after tax", "pat"])
                dep        = v(["depreciation", "amortization", "d&a"])
                if ebitda == 0 and ebit:
                    ebitda = ebit + dep
                interest   = abs(v(["interest expense", "finance cost"]))
                tax        = abs(v(["tax", "income tax"]))

                cfo   = v(["operating cash flow", "cash from operations", "cfo", "net cash from operating"])
                capex = abs(v(["capital expenditure", "capex", "purchase of ppe", "additions"]))
                fcf   = v(["free cash flow", "fcf"]) or (cfo - capex)

                ta  = v(["total assets"])
                eq  = v(["equity", "shareholders equity", "stockholders equity"])
                debt = v(["total debt", "borrowings", "loans"]) or v(["long term debt"]) + v(["short term debt"])
                cash = v(["cash", "cash and equivalents", "cash and bank"])
                ca   = v(["current assets"])
                cl   = v(["current liabilities"])
                inv  = v(["inventory", "inventories", "stock"])
                rec  = v(["receivables", "accounts receivable", "trade receivables"])
                pay  = v(["payables", "accounts payable", "trade payables"])

                result["income"].append({
                    "year": int(str(yr)), "revenue": revenue, "cogs": cogs, "gross_profit": gp,
                    "ebitda": ebitda, "ebit": ebit, "net_income": ni,
                    "interest_expense": interest, "tax_expense": tax, "depreciation": dep,
                })
                result["balance_sheet"].append({
                    "year": int(str(yr)), "total_assets": ta, "total_equity": eq,
                    "debt": debt, "cash": cash, "current_assets": ca,
                    "current_liabilities": cl, "inventory": inv, "receivables": rec, "payables": pay,
                })
                result["cashflow"].append({"year": int(str(yr)), "cfo": cfo, "capex": capex, "fcf": fcf})

            for key in ["income", "balance_sheet", "cashflow"]:
                result[key] = sorted(result[key], key=lambda x: x["year"])

            result["profile"] = {"name": "Private Company (Uploaded)", "currency": "USD", "sector": "—", "industry": "—"}
            result["kpis"] = DataFetcher()._calc_kpis(result)
            result["market_data"] = {}
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def _safe(row, keys):
    for k in keys:
        if k in row.index:
            v = row[k]
            if pd.notna(v):
                return float(v)
    return None

# Singleton instance
_fetcher_instance = None

def get_fetcher() -> DataFetcher:
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = DataFetcher()
    return _fetcher_instance
