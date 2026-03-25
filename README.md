# ⬡ PRO ANALYST — AI Financial Intelligence Dashboard

> **Institutional-grade financial analysis for any listed or private company worldwide.**  
> Powered by Yahoo Finance · Financial Modeling Prep · World Bank · Anthropic Claude AI

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red)
![Claude](https://img.shields.io/badge/AI-Claude_Opus-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📸 What It Does

- **Any listed company** from PSX, NSE, BSE, NYSE, NASDAQ, LSE, TADAWUL, DFM, HKEX and 10+ more exchanges
- **Private companies** — upload Excel/CSV financials and get full analysis
- **30+ KPIs** auto-calculated: margins, returns, leverage, liquidity, efficiency, valuation
- **AI equity research report** — Claude generates investment-grade commentary in seconds
- **Macro & micro-economic risk** — live World Bank data, country indicators, risk register
- **Peer comparison** — heatmaps, ranked bars, spider charts vs up to 3 peers
- **Scenario analysis** — Bull / Base / Bear case toggle
- **Weighted scoring model** — 0–100 overall financial health score

---

## 🗂️ Project Structure

```
pro-analyst-dashboard/
│
├── app.py                          # ← Streamlit entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore
│
├── .streamlit/
│   ├── config.toml                 # Streamlit theme & server config
│   └── secrets.toml.example        # API keys template (DO NOT commit secrets.toml)
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD pipeline
│
├── data_fetchers/
│   └── fetcher.py                  # Unified data fetcher (yfinance + FMP + World Bank)
│
├── ai_engine/
│   └── analyst.py                  # Anthropic Claude AI analysis engine
│
├── utils/
│   ├── benchmarks.py               # Industry benchmark database (40+ sectors)
│   └── charts.py                   # Plotly chart factory
│
├── pages/
│   └── main_dashboard.py           # Full Streamlit UI (8 tabs, sidebar, upload)
│
└── tests/
    └── test_core.py                # Unit tests
```

---

## 🚀 FULL DEPLOYMENT GUIDE

### STEP 1 — Prerequisites

Install these before starting:
- Python 3.11+ → https://python.org
- Git → https://git-scm.com
- GitHub account → https://github.com
- Streamlit account → https://share.streamlit.io (free)

---

### STEP 2 — Get Your API Keys

You need **at minimum** the Anthropic key. Others are optional but improve data quality.

| Service | Required? | Free Tier | Get Key |
|---------|-----------|-----------|---------|
| **Anthropic Claude** | ✅ Yes | Paid ($5 starter) | https://console.anthropic.com |
| **Financial Modeling Prep** | Recommended | 250 calls/day | https://financialmodelingprep.com |
| **Alpha Vantage** | Optional | 25 calls/day | https://alphavantage.co |
| **FRED (Federal Reserve)** | Optional | Free | https://fred.stlouisfed.org/docs/api |
| **Yahoo Finance** | Auto | Free (no key) | Built-in |
| **World Bank** | Auto | Free (no key) | Built-in |

---

### STEP 3 — Local Setup

```bash
# 1. Clone or create repo
git clone https://github.com/yourusername/pro-analyst-dashboard.git
cd pro-analyst-dashboard

# 2. Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
# Now edit .env and add your API keys

# 5. Create Streamlit secrets folder
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your API keys

# 6. Run locally
streamlit run app.py
```

Open → http://localhost:8501

---

### STEP 4 — GitHub Setup

```bash
# Initialize git (if not already)
git init
git branch -M main

# Stage all files (NEVER commit .env or secrets.toml)
git add .
git commit -m "feat: initial PRO ANALYST dashboard"

# Create GitHub repo (go to github.com → New Repository)
# Name: pro-analyst-dashboard
# Visibility: Public or Private (Private recommended if commercial)

# Push to GitHub
git remote add origin https://github.com/yourusername/pro-analyst-dashboard.git
git push -u origin main
```

**⚠️ CRITICAL:** Your `.gitignore` already excludes `.env` and `secrets.toml`. Never commit API keys.

---

### STEP 5 — Streamlit Cloud Deployment

1. **Go to** → https://share.streamlit.io
2. Click **"New app"**
3. **Connect GitHub** if not already connected
4. **Repository:** select `pro-analyst-dashboard`
5. **Branch:** `main`
6. **Main file path:** `app.py`
7. Click **Advanced settings** → **Secrets**

Paste this into the secrets box (replace with your real keys):

```toml
[api_keys]
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
FMP_API_KEY = "your-fmp-key-here"
ALPHA_VANTAGE_API_KEY = "your-av-key-here"
FRED_API_KEY = "your-fred-key-here"

[app]
ENV = "production"
CACHE_TTL = 3600
MAX_PEERS = 5
PRIMARY_DATA_SOURCE = "fmp"
```

8. Click **"Deploy!"**

Your app will be live at: `https://your-app-name.streamlit.app`

Deployment takes ~2–5 minutes.

---

### STEP 6 — Continuous Deployment

After initial setup, every `git push` to `main` will:
1. Trigger GitHub Actions CI (runs tests, lint checks)
2. Streamlit Cloud auto-redeploys from `main`

```bash
# Make changes → push → auto-deploy
git add .
git commit -m "feat: add new feature"
git push origin main
# GitHub Actions runs → Streamlit redeploys automatically
```

---

## 📊 How to Use the Dashboard

### Listed Companies
1. Select **exchange** (e.g., 🇵🇰 Pakistan PSX)
2. Enter **ticker** (e.g., `NESTLE` for Nestle Pakistan)
3. Click **Load**
4. Explore 8 tabs: Overview, Profitability, Cash Flow, Balance Sheet, Peers, Valuation, Macro & Risk, AI Report
5. Add up to 3 peer companies for comparison
6. Click **Generate AI Analysis** for full research report

### Ticker Format by Exchange
| Exchange | Format | Example |
|----------|--------|---------|
| PSX (Pakistan) | TICKER | `NESTLE`, `ENGRO`, `LUCK` |
| NSE (India) | TICKER | `RELIANCE`, `TCS`, `INFY` |
| NYSE/NASDAQ | TICKER | `AAPL`, `MSFT`, `AMZN` |
| LSE (UK) | TICKER | `BP`, `HSBA`, `ULVR` |
| TADAWUL (Saudi) | TICKER | `2222` (Aramco) |
| HKEX | TICKER | `0700` (Tencent) |

### Private Companies
1. Select **Private Company (Upload)**
2. Download **template** → fill in your financials
3. Upload the Excel file
4. Enter company name, industry, country
5. Click **Analyze**

---

## 🔧 Configuration

### Change Default Data Source
In `.env` or `secrets.toml`:
```
PRIMARY_DATA_SOURCE=fmp        # Use FMP (best for global stocks)
PRIMARY_DATA_SOURCE=yfinance   # Use Yahoo Finance (free fallback)
```

### Cache Duration
```
CACHE_TTL_SECONDS=3600    # 1 hour (recommended for free APIs)
CACHE_TTL_SECONDS=86400   # 24 hours (for static analysis)
```

### Adjust Scoring Weights
Edit `ai_engine/analyst.py` → `calc_score()`:
```python
total = (
    profitability  * 0.22 +   # ← adjust weights here
    growth         * 0.20 +
    cashflow       * 0.18 +
    balance_sheet  * 0.18 +
    efficiency     * 0.12 +
    valuation      * 0.10 -
    risk_penalty
)
```

### Add Industry Benchmarks
Edit `utils/benchmarks.py`:
```python
INDUSTRY_BENCHMARKS["Your Industry"] = {
    "avg_revenue_growth": 0.10,
    "avg_ebitda_margin":  0.25,
    "avg_net_margin":     0.14,
    "avg_roe":            0.22,
    "avg_roic":           0.16,
    "avg_debt_ebitda":    2.0,
    "avg_current_ratio":  1.5,
    "avg_pe":             22.0,
    "avg_ev_ebitda":      14.0,
    "cyclicality":        "Medium",
}
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Run specific test class
pytest tests/test_core.py::TestAnalyst -v
```

---

## 🚨 Troubleshooting

### "No data found" for a ticker
- Try the full Yahoo Finance format: `NESTLE.KA` for PSX, `RELIANCE.NS` for NSE
- Some exchanges have limited data on yfinance — add FMP key for better coverage
- For Saudi stocks, use the numeric code (e.g., `2222` for Aramco)

### "API key not configured"
- For local: check your `.env` file has the key without quotes around variable name
- For Streamlit Cloud: go to App Settings → Secrets and verify the key is pasted correctly

### App crashes on startup
- Run `pip install -r requirements.txt` again — version conflicts can occur
- Check Python version: `python --version` must be 3.11+

### Streamlit deployment fails
- Check GitHub Actions tab for error details
- Ensure `requirements.txt` is committed to repo
- Verify `app.py` is at root level (not inside a subfolder)

---

## 📁 Excel Upload Template Guide

The upload template has rows for:

**Income Statement:** Revenue, COGS, Gross Profit, EBITDA, EBIT, Net Income, D&A, Interest, Tax  
**Balance Sheet:** Total Assets, Equity, Debt, Cash, Current Assets/Liabilities, Inventory, Receivables, Payables  
**Cash Flow:** Operating CF, Capex, Free Cash Flow

Column headers should be **years** (e.g., 2019, 2020, 2021, 2022, 2023).  
First column should be the metric/row name.

Download the template from the sidebar → it's pre-filled with sample data.

---

## 📄 License

MIT License — free for personal and commercial use.

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'feat: add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open Pull Request

---

## 🗺️ Roadmap

- [ ] Real-time price WebSocket feed
- [ ] Portfolio-level analysis (multi-company aggregate)
- [ ] PDF export with charts
- [ ] Email/Slack alerts for risk flag changes
- [ ] Historical data back to 10 years
- [ ] DCF valuation model
- [ ] Management discussion parser (PDF annual report ingestion)
- [ ] Screener: filter all PSX/NSE stocks by KPI criteria

---

*Built with Streamlit · Anthropic Claude · Yahoo Finance · Plotly · World Bank API*
