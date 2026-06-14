"""
US Politician Stock Trades Dashboard
====================================
Ein Dashboard, das Aktien-Käufe und -Verkäufe von US-Politikern (Senat + Haus)
dokumentiert. Datenquelle: Financial Modeling Prep (FMP) API.

Rechtliche Grundlage: STOCK Act (2012) -> verpflichtet Kongressmitglieder,
Trades > 1.000 USD innerhalb von 45 Tagen offenzulegen.

Start:  streamlit run app.py

Kurshistorie: yfinance (pip install yfinance) – kostenlos, kein API-Key nötig.
"""

import os
import sqlite3
import datetime as dt
import requests
import pandas as pd
import streamlit as st

# ── optionale Abhängigkeit für Kurshistorie ──────────────────────────────────
try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False

# Pfad zur lokalen Historien-Datenbank (liegt neben app.py).
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades_history.db")

# --------------------------------------------------------------------------
# Theme-Konfiguration
# --------------------------------------------------------------------------
def apply_theme(dark: bool):
    """Injiziert CSS für Dark- oder Light-Mode."""
    if dark:
        bg        = "#0e1117"
        card_bg   = "#1a1f2e"
        sidebar   = "#161b2a"
        text      = "#e8eaf0"
        subtext   = "#9ba3b8"
        border    = "#2d3348"
        accent    = "#4f8ef7"
        buy_color = "#22c55e"
        sell_color= "#ef4444"
        bar_buy   = "#166534"
        bar_sell  = "#7f1d1d"
        metric_bg = "#1e2536"
        tag_buy   = "#14532d"
        tag_sell  = "#7f1d1d"
    else:
        bg        = "#f8f9fc"
        card_bg   = "#ffffff"
        sidebar   = "#f0f2f8"
        text      = "#1a1d2e"
        subtext   = "#5a6180"
        border    = "#d1d9f0"
        accent    = "#2563eb"
        buy_color = "#16a34a"
        sell_color= "#dc2626"
        bar_buy   = "#bbf7d0"
        bar_sell  = "#fecaca"
        metric_bg = "#eff2ff"
        tag_buy   = "#dcfce7"
        tag_sell  = "#fee2e2"

    st.markdown(f"""
    <style>
    /* ── Globaler Hintergrund ─────────────────────────────── */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: {bg};
        color: {text};
    }}
    [data-testid="stHeader"] {{
        background-color: {bg};
    }}
    /* ── Sidebar ──────────────────────────────────────────── */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: {sidebar};
        border-right: 1px solid {border};
    }}
    [data-testid="stSidebar"] * {{
        color: {text} !important;
    }}
    /* ── Metriken ─────────────────────────────────────────── */
    [data-testid="stMetric"] {{
        background-color: {metric_bg};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 12px 16px;
    }}
    [data-testid="stMetricValue"] {{
        color: {text} !important;
        font-weight: 700;
    }}
    [data-testid="stMetricLabel"] {{
        color: {subtext} !important;
    }}
    /* ── Tabs ─────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {card_bg};
        border-radius: 8px;
        border: 1px solid {border};
        padding: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {subtext};
        border-radius: 6px;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {accent} !important;
        color: #fff !important;
    }}
    /* ── Dataframe ────────────────────────────────────────── */
    [data-testid="stDataFrame"] {{
        border: 1px solid {border};
        border-radius: 8px;
        overflow: hidden;
    }}
    /* ── Buttons ──────────────────────────────────────────── */
    .stButton > button {{
        background-color: {accent};
        color: #fff;
        border: none;
        border-radius: 6px;
    }}
    .stButton > button:hover {{
        opacity: 0.85;
    }}
    /* ── Inputs ───────────────────────────────────────────── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stDateInput > div > div > input {{
        background-color: {card_bg};
        border: 1px solid {border};
        color: {text};
        border-radius: 6px;
    }}
    /* ── Kauf/Verkauf-Tags ────────────────────────────────── */
    .tag-buy {{
        background: {tag_buy}; color: {buy_color};
        border-radius: 4px; padding: 2px 8px; font-weight: 600;
        font-size: 0.75rem;
    }}
    .tag-sell {{
        background: {tag_sell}; color: {sell_color};
        border-radius: 4px; padding: 2px 8px; font-weight: 600;
        font-size: 0.75rem;
    }}
    /* ── Kaufdruck-Balken ─────────────────────────────────── */
    .pressure-row {{
        display: flex; align-items: center; gap: 10px;
        margin-bottom: 8px; padding: 8px 12px;
        background: {card_bg}; border: 1px solid {border};
        border-radius: 8px;
    }}
    .ticker-label {{
        font-weight: 700; color: {accent};
        min-width: 60px; font-size: 0.95rem;
    }}
    .bar-track {{
        flex: 1; height: 14px; border-radius: 7px;
        background: {border}; overflow: hidden;
        display: flex;
    }}
    .bar-buy   {{ background: {buy_color};   height: 100%; }}
    .bar-sell  {{ background: {sell_color};  height: 100%; }}
    .pct-label {{ font-size: 0.78rem; color: {subtext}; min-width: 80px; text-align: right; }}
    .vol-label {{ font-size: 0.78rem; color: {subtext}; min-width: 90px; text-align: right; }}
    /* ── Allgemein ────────────────────────────────────────── */
    h1, h2, h3, h4 {{ color: {text} !important; }}
    p, span, label {{ color: {subtext}; }}
    hr {{ border-color: {border}; }}
    .stCaption {{ color: {subtext} !important; }}
    </style>
    """, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------
def get_api_key() -> str | None:
    key = os.environ.get("FMP_API_KEY")
    if not key:
        try:
            key = st.secrets["FMP_API_KEY"]
        except Exception:
            key = None
    return key


FMP_STABLE = "https://financialmodelingprep.com/stable"
LATEST_ENDPOINTS = [
    f"{FMP_STABLE}/senate-latest",
    f"{FMP_STABLE}/house-latest",
]
PAGES_TO_FETCH = 3


# --------------------------------------------------------------------------
# Daten laden (FMP)
# --------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_all(api_key: str) -> pd.DataFrame:
    frames = []
    errors = []
    for base in LATEST_ENDPOINTS:
        for page in range(PAGES_TO_FETCH):
            url = f"{base}?apikey={api_key}" if page == 0 else f"{base}?page={page}&apikey={api_key}"
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and data:
                        frames.append(pd.DataFrame(data))
                    else:
                        break
                elif resp.status_code == 402:
                    if page == 0:
                        errors.append("HTTP 402 – Endpoint nicht im Free-Plan enthalten.")
                    break
                elif resp.status_code == 401:
                    errors.append("HTTP 401 – API-Key ungültig.")
                    break
                elif resp.status_code == 403:
                    errors.append("HTTP 403 – Endpoint nicht im aktuellen Plan.")
                    break
                else:
                    errors.append(f"HTTP {resp.status_code} bei {base}")
                    break
            except Exception as e:
                errors.append(str(e))
                break

    if not frames:
        for e in set(errors):
            st.warning(e)
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    rename_map = {
        "firstName": "first_name", "lastName": "last_name",
        "symbol": "ticker", "transactionDate": "transaction_date",
        "dateRecieved": "disclosure_date", "disclosureDate": "disclosure_date",
        "type": "transaction_type", "assetDescription": "asset",
        "assetType": "asset_type", "amount": "amount_range",
        "owner": "owner", "district": "district", "link": "source_url",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if "first_name" in df.columns and "last_name" in df.columns:
        df["politician"] = (
            df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        ).str.strip()
    elif "office" in df.columns:
        df["politician"] = df["office"]
    else:
        df["politician"] = "Unbekannt"

    def chamber_from_district(d):
        if not isinstance(d, str) or d.strip() == "":
            return "Senat"
        return "Haus" if any(ch.isdigit() for ch in d) else "Senat"

    if "district" in df.columns:
        df["chamber"] = df["district"].apply(chamber_from_district)
    else:
        df["chamber"] = "Unbekannt"

    for col in ["ticker", "transaction_date", "disclosure_date",
                "transaction_type", "asset", "asset_type", "amount_range",
                "owner", "source_url"]:
        if col not in df.columns:
            df[col] = None

    for col in ["transaction_date", "disclosure_date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["amount_mid"] = df["amount_range"].apply(parse_amount_mid)
    df["direction"] = df["transaction_type"].apply(classify_direction)

    keep = ["politician", "chamber", "district", "owner", "ticker", "asset",
            "asset_type", "direction", "transaction_type", "amount_range",
            "amount_mid", "transaction_date", "disclosure_date", "source_url"]
    keep = [c for c in keep if c in df.columns]
    return df[keep]


# --------------------------------------------------------------------------
# Historien-Datenbank (SQLite)
# --------------------------------------------------------------------------
def make_trade_id(row) -> str:
    import hashlib
    parts = [str(row.get(k, "")) for k in
             ["politician", "ticker", "transaction_date", "amount_range", "direction", "owner"]]
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id TEXT PRIMARY KEY,
            politician TEXT, chamber TEXT, district TEXT, owner TEXT,
            ticker TEXT, asset TEXT, asset_type TEXT, direction TEXT,
            transaction_type TEXT, amount_range TEXT, amount_mid REAL,
            transaction_date TEXT, disclosure_date TEXT,
            source_url TEXT, first_seen TEXT
        )
    """)
    con.commit()
    con.close()


def save_trades(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    init_db()
    con = sqlite3.connect(DB_PATH)
    now = dt.datetime.now().isoformat(timespec="seconds")
    added = 0
    for _, row in df.iterrows():
        tid = make_trade_id(row)
        cur = con.execute(
            """INSERT OR IGNORE INTO trades
            (trade_id, politician, chamber, district, owner, ticker, asset,
             asset_type, direction, transaction_type, amount_range, amount_mid,
             transaction_date, disclosure_date, source_url, first_seen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, row.get("politician"), row.get("chamber"), row.get("district"),
             row.get("owner"), row.get("ticker"), row.get("asset"),
             row.get("asset_type"), row.get("direction"), row.get("transaction_type"),
             row.get("amount_range"),
             float(row["amount_mid"]) if pd.notna(row.get("amount_mid")) else None,
             str(row.get("transaction_date")) if pd.notna(row.get("transaction_date")) else None,
             str(row.get("disclosure_date")) if pd.notna(row.get("disclosure_date")) else None,
             row.get("source_url"), now),
        )
        added += cur.rowcount
    con.commit()
    con.close()
    return added


def load_history() -> pd.DataFrame:
    init_db()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM trades", con)
    con.close()
    if not df.empty:
        for col in ["transaction_date", "disclosure_date"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def history_count() -> int:
    init_db()
    con = sqlite3.connect(DB_PATH)
    n = con.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    con.close()
    return n


def parse_amount_mid(value) -> float:
    if not isinstance(value, str):
        return float("nan")
    import re
    nums = re.findall(r"[\d,]+", value.replace("$", ""))
    nums = [float(n.replace(",", "")) for n in nums if n.replace(",", "").isdigit()]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    if len(nums) == 1:
        return nums[0]
    return float("nan")


def classify_direction(t) -> str:
    if not isinstance(t, str):
        return "Unbekannt"
    t = t.lower()
    if "purchase" in t or "buy" in t:
        return "Kauf"
    if "sale" in t or "sell" in t:
        return "Verkauf"
    return "Sonstige"


def demo_data() -> pd.DataFrame:
    rows = [
        ("Jane Doe", "Senat", "RI", "Self", "AAPL", "Apple Inc", "Stock",
         "Kauf", "Purchase", "$15,001 - $50,000", 32500, "2026-05-02", "2026-05-20", "https://example.com/1"),
        ("Jane Doe", "Senat", "RI", "Self", "MSFT", "Microsoft Corp", "Stock",
         "Verkauf", "Sale", "$1,001 - $15,000", 8000, "2026-05-10", "2026-05-28", "https://example.com/2"),
        ("John Smith", "Haus", "TX08", "Self", "NVDA", "NVIDIA Corp", "Stock",
         "Kauf", "Purchase", "$50,001 - $100,000", 75000, "2026-04-18", "2026-05-30", "https://example.com/3"),
        ("John Smith", "Haus", "TX08", "Spouse", "TSLA", "Tesla Inc", "Stock",
         "Kauf", "Purchase", "$1,001 - $15,000", 8000, "2026-04-22", "2026-06-01", "https://example.com/4"),
        ("Maria Lopez", "Senat", "CA", "Self", "NVDA", "NVIDIA Corp", "Stock",
         "Verkauf", "Sale", "$100,001 - $250,000", 175000, "2026-05-15", "2026-06-05", "https://example.com/5"),
        ("Maria Lopez", "Senat", "CA", "Joint", "AMZN", "Amazon.com Inc", "Stock",
         "Kauf", "Purchase", "$15,001 - $50,000", 32500, "2026-05-20", "2026-06-08", "https://example.com/6"),
        ("Robert King", "Haus", "FL12", "Self", "AAPL", "Apple Inc", "Stock",
         "Verkauf", "Sale", "$1,001 - $15,000", 8000, "2026-03-30", "2026-05-12", "https://example.com/7"),
        ("Robert King", "Haus", "FL12", "Self", "TSLA", "Tesla Inc", "Stock",
         "Kauf", "Purchase", "$50,001 - $100,000", 75000, "2026-03-15", "2026-05-01", "https://example.com/8"),
        ("Jane Doe", "Senat", "RI", "Self", "NVDA", "NVIDIA Corp", "Stock",
         "Kauf", "Purchase", "$50,001 - $100,000", 75000, "2026-06-01", "2026-06-10", "https://example.com/9"),
        ("Maria Lopez", "Senat", "CA", "Self", "AAPL", "Apple Inc", "Stock",
         "Kauf", "Purchase", "$15,001 - $50,000", 32500, "2026-06-03", "2026-06-12", "https://example.com/10"),
    ]
    cols = ["politician", "chamber", "district", "owner", "ticker", "asset",
            "asset_type", "direction", "transaction_type", "amount_range",
            "amount_mid", "transaction_date", "disclosure_date", "source_url"]
    df = pd.DataFrame(rows, columns=cols)
    for c in ["transaction_date", "disclosure_date"]:
        df[c] = pd.to_datetime(df[c])
    return df


# --------------------------------------------------------------------------
# Kurshistorie via yfinance
# --------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_price_history(ticker: str, period: str) -> pd.DataFrame:
    """Lädt Kurshistorie via yfinance. Gibt leeres DataFrame bei Fehler zurück."""
    if not YFINANCE_OK:
        return pd.DataFrame()
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            return pd.DataFrame()
        hist = hist[["Close"]].copy()
        hist.index = pd.to_datetime(hist.index).tz_localize(None)
        hist.columns = ["Kurs (USD)"]
        return hist
    except Exception:
        return pd.DataFrame()


# --------------------------------------------------------------------------
# Unternehmenslogo & Name
# --------------------------------------------------------------------------
# Clearbit Logo API: https://logo.clearbit.com/<domain>  – kostenlos, kein Key.
# Fallback: leeres Bild-Platzhalter.
# Wir pflegen eine Ticker→Domain-Tabelle für die häufigsten Werte;
# unbekannte Ticker bekommen keinen Logo-Versuch (vermeidet 404-Spam).
TICKER_DOMAIN: dict[str, str] = {
    "AAPL":  "apple.com",
    "MSFT":  "microsoft.com",
    "NVDA":  "nvidia.com",
    "GOOGL": "google.com",
    "GOOG":  "google.com",
    "AMZN":  "amazon.com",
    "META":  "meta.com",
    "TSLA":  "tesla.com",
    "JPM":   "jpmorganchase.com",
    "V":     "visa.com",
    "MA":    "mastercard.com",
    "UNH":   "unitedhealthgroup.com",
    "JNJ":   "jnj.com",
    "WFC":   "wellsfargo.com",
    "BAC":   "bankofamerica.com",
    "GS":    "goldmansachs.com",
    "MS":    "morganstanley.com",
    "BX":    "blackstone.com",
    "ORCL":  "oracle.com",
    "IBM":   "ibm.com",
    "ADBE":  "adobe.com",
    "AMD":   "amd.com",
    "QCOM":  "qualcomm.com",
    "AVGO":  "broadcom.com",
    "INTC":  "intel.com",
    "MU":    "micron.com",
    "PLTR":  "palantir.com",
    "CRWD":  "crowdstrike.com",
    "DDOG":  "datadoghq.com",
    "TEAM":  "atlassian.com",
    "WDAY":  "workday.com",
    "PYPL":  "paypal.com",
    "SQ":    "squareup.com",
    "UBER":  "uber.com",
    "DASH":  "doordash.com",
    "ABNB":  "airbnb.com",
    "BKNG":  "bookingholdings.com",
    "AMGN":  "amgen.com",
    "REGN":  "regeneron.com",
    "BIIB":  "biogen.com",
    "ABBV":  "abbvie.com",
    "PFE":   "pfizer.com",
    "MRK":   "merck.com",
    "LLY":   "lilly.com",
    "GILD":  "gilead.com",
    "BSX":   "bostonscientific.com",
    "ETN":   "eaton.com",
    "HON":   "honeywell.com",
    "GE":    "ge.com",
    "GEHC":  "gehealthcare.com",
    "SHW":   "sherwin-williams.com",
    "CLX":   "clorox.com",
    "PEP":   "pepsico.com",
    "KO":    "coca-cola.com",
    "SBUX":  "starbucks.com",
    "MCD":   "mcdonalds.com",
    "DPZ":   "dominos.com",
    "HSY":   "thehersheycompany.com",
    "SJM":   "jmsmucker.com",
    "CAG":   "conagrabrands.com",
    "T":     "att.com",
    "VZ":    "verizon.com",
    "CMCSA": "comcast.com",
    "DTE":   "dteenergy.com",
    "LNG":   "cheniere.com",
    "DVN":   "devonenergy.com",
    "CTRA":  "coterra.com",
    "AXP":   "americanexpress.com",
    "CB":    "chubb.com",
    "ERIE":  "erieindemnity.com",
    "PNC":   "pnc.com",
    "FITB":  "53.com",
    "LPLA":  "lpl.com",
    "ARES":  "aresmgmt.com",
    "CVNA":  "carvana.com",
    "AZO":   "autozone.com",
    "W":     "wayfair.com",
    "RKT":   "rocketcompanies.com",
    "APP":   "applovin.com",
    "TTD":   "thetradedesk.com",
    "PTON":  "onepeloton.com",
    "EA":    "ea.com",
    "ACN":   "accenture.com",
    "TYL":   "tylertech.com",
    "ROP":   "ropertech.com",
    "VRSK":  "verisk.com",
    "FDS":   "factset.com",
    "BR":    "broadridge.com",
    "GPN":   "globalpayments.com",
    "FBK":   "firstbankonline.com",
    "INDB":  "rocklandtrust.com",
    "TCBI":  "texascapitalbank.com",
    "ABT":   "abbott.com",
    "CTVA":  "corteva.com",
    "STE":   "steris.com",
    "TRMB":  "trimble.com",
    "HQY":   "healthequity.com",
    "CIEN":  "ciena.com",
    "VIAV":  "viavi.com",
    "FLEX":  "flex.com",
    "TEL":   "te.com",
    "ST":    "sensata.com",
    "COO":   "coopercos.com",
    "LGND":  "ligand.com",
    "NOVT":  "novanta.com",
    "TOST":  "toasttab.com",
    "ETOR":  "etoro.com",
    "GIL":   "gildan.com",
    "BEP":   "brookfield.com",
    "STZ":   "cbrands.com",
    "IBM":   "ibm.com",
}


def logo_url(ticker: str) -> str | None:
    """Gibt die Clearbit-Logo-URL für einen Ticker zurück, oder None."""
    domain = TICKER_DOMAIN.get(ticker.upper())
    if domain:
        return f"https://logo.clearbit.com/{domain}?size=32"
    return None


def logo_img_tag(ticker: str, size: int = 28) -> str:
    """HTML <img>-Tag für das Logo, mit Fallback auf Ticker-Initialen."""
    url = logo_url(ticker)
    if url:
        return (
            f'<img src="{url}" width="{size}" height="{size}" '
            f'style="border-radius:4px;object-fit:contain;vertical-align:middle;" '
            f'onerror="this.style.display=\'none\'">'
        )
    return ""


def company_name_for(ticker: str, name_map: dict[str, str]) -> str:
    """Gibt den Unternehmensnamen aus name_map zurück, oder den Ticker selbst."""
    return name_map.get(ticker, ticker)


# --------------------------------------------------------------------------
# Kaufdruck-Widget
# --------------------------------------------------------------------------
def render_buy_pressure(top_df: pd.DataFrame, name_map: dict[str, str] | None = None):
    """Rendert einen visuellen Kaufdruck-Indikator, sortiert von meistgekauft bis meistverkauft."""
    if name_map is None:
        name_map = {}

    st.markdown("### 🔥 Kaufdruck-Indikator")
    st.caption(
        "Sortiert von meistgekauft (oben) bis meistverkauft (unten). "
        "Breite des Balkens = Anteil am Gesamtvolumen (Käufe grün, Verkäufe rot)."
    )

    # Nur Zeilen mit Volumendaten; nach Kaufanteil absteigend sortieren
    valid = top_df[
        (top_df["kauf_vol"].fillna(0) + top_df["verkauf_vol"].fillna(0)) > 0
    ].copy()
    valid["_buy_pct"] = valid.apply(
        lambda r: r["kauf_vol"] / (r["kauf_vol"] + r["verkauf_vol"]) * 100
        if (r["kauf_vol"] + r["verkauf_vol"]) > 0 else 0, axis=1
    )
    valid = valid.sort_values("_buy_pct", ascending=False)

    if valid.empty:
        st.info("Keine Volumendaten für den gewählten Zeitraum.")
        return

    for _, row in valid.iterrows():
        ticker   = row["ticker"]
        buy_vol  = row.get("kauf_vol", 0) or 0
        sell_vol = row.get("verkauf_vol", 0) or 0
        total    = buy_vol + sell_vol
        buy_pct  = buy_vol / total * 100
        sell_pct = 100 - buy_pct
        cname    = company_name_for(ticker, name_map)
        logo     = logo_url(ticker)

        # Eine Zeile = 6 Spalten: Logo | Ticker+Name | Kauf-Balken | Pct | Verkauf-Balken | Volumen
        c_logo, c_name, c_buy_bar, c_pct, c_sell_bar, c_vol = st.columns(
            [0.5, 3, 4, 2, 4, 2]
        )
        with c_logo:
            if logo:
                st.image(logo, width=28)
        with c_name:
            st.markdown(
                f"**{ticker}**  \n"
                f"<span style='font-size:0.75rem;opacity:0.65'>{cname}</span>",
                unsafe_allow_html=True,
            )
        with c_buy_bar:
            st.markdown(
                f"<div style='margin-top:8px'>"
                f"<div style='height:14px;border-radius:7px;background:#22c55e;"
                f"width:{buy_pct:.1f}%;min-width:2px'></div></div>",
                unsafe_allow_html=True,
            )
        with c_pct:
            st.markdown(
                f"<div style='margin-top:4px;font-size:0.8rem'>"
                f"🟢 {buy_pct:.0f}% &nbsp; 🔴 {sell_pct:.0f}%</div>",
                unsafe_allow_html=True,
            )
        with c_sell_bar:
            st.markdown(
                f"<div style='margin-top:8px'>"
                f"<div style='height:14px;border-radius:7px;background:#ef4444;"
                f"width:{sell_pct:.1f}%;min-width:2px'></div></div>",
                unsafe_allow_html=True,
            )
        with c_vol:
            st.markdown(
                f"<div style='margin-top:4px;font-size:0.8rem;opacity:0.7'>"
                f"${total:,.0f}</div>",
                unsafe_allow_html=True,
            )
        st.divider()


# --------------------------------------------------------------------------
# Seitenaufbau
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="US-Politiker Aktien-Trades",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme-Toggle (muss VOR apply_theme stehen) ────────────────────────────
with st.sidebar:
    dark_mode = st.toggle("🌙 Dark Mode", value=True)

apply_theme(dark_mode)

# ── Titel ─────────────────────────────────────────────────────────────────
st.markdown("# 🏛️ US-Politiker Aktien-Trades Dashboard")
st.caption(
    "Käufe und Verkäufe von Mitgliedern des US-Kongresses (Offenlegung gemäß STOCK Act). "
    "Daten via Financial Modeling Prep. Beträge werden nur als Spannen gemeldet."
)

api_key = get_api_key()

with st.sidebar:
    st.header("Datenquelle")
    use_demo = st.toggle("Demo-Daten verwenden", value=not bool(api_key))
    if not api_key and not use_demo:
        st.error("Kein FMP_API_KEY gefunden. Aktiviere Demo-Daten oder hinterlege einen Key.")
    st.markdown("---")


def aktualisieren(api_key) -> int:
    frisch = normalize(fetch_all(api_key))
    return save_trades(frisch)


# ── Daten beschaffen ──────────────────────────────────────────────────────
if use_demo:
    df = demo_data()
    st.info("📌 Es werden **Demo-Daten** angezeigt. Hinterlege einen API-Key für echte Daten.")
else:
    if "auto_refreshed" not in st.session_state:
        with st.spinner("Aktualisiere Daten von FMP …"):
            try:
                neu = aktualisieren(api_key)
                st.session_state["auto_refreshed"] = True
                st.session_state["last_added"] = neu
            except Exception as e:
                st.warning(f"Automatische Aktualisierung fehlgeschlagen: {e}")

    with st.sidebar:
        st.header("Historie")
        st.metric("Gespeicherte Trades", history_count())
        if st.session_state.get("last_added") is not None:
            st.caption(f"Zuletzt neu hinzugefügt: {st.session_state['last_added']}")
        if st.button("🔄 Jetzt aktualisieren"):
            with st.spinner("Hole neue Trades …"):
                neu = aktualisieren(api_key)
                st.session_state["last_added"] = neu
            st.success(f"{neu} neue Trades gespeichert.")
            st.rerun()
        st.markdown("---")

    df = load_history()
    if df.empty:
        st.error("Noch keine Daten. Prüfe den API-Key oder nutze den Aktualisieren-Knopf.")
        st.stop()

# ── Deduplizieren ─────────────────────────────────────────────────────────
df = df.drop_duplicates(
    subset=["politician", "ticker", "transaction_date", "amount_range", "direction"]
)

# ── Sidebar-Filter ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filter")
    politicians = sorted(df["politician"].dropna().unique())
    sel_pol = st.multiselect("Politiker", politicians)

    chambers = sorted(df["chamber"].dropna().unique())
    sel_cham = st.multiselect("Kammer", chambers, default=chambers)

    directions = sorted(df["direction"].dropna().unique())
    sel_dir = st.multiselect("Art", directions, default=directions)

    tickers = sorted([t for t in df["ticker"].dropna().unique() if t])
    sel_tick = st.multiselect("Ticker", tickers)

    valid_dates = df["transaction_date"].dropna()
    if not valid_dates.empty:
        dmin, dmax = valid_dates.min().date(), valid_dates.max().date()
        date_range = st.date_input(
            "Transaktionszeitraum", (dmin, dmax),
            min_value=dmin, max_value=dmax
        )
    else:
        date_range = None

# ── Filter anwenden ───────────────────────────────────────────────────────
f = df.copy()
if sel_pol:
    f = f[f["politician"].isin(sel_pol)]
if sel_cham:
    f = f[f["chamber"].isin(sel_cham)]
if sel_dir:
    f = f[f["direction"].isin(sel_dir)]
if sel_tick:
    f = f[f["ticker"].isin(sel_tick)]
if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    f = f[(f["transaction_date"].dt.date >= start) &
          (f["transaction_date"].dt.date <= end)]

# ── Kennzahlen ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Trades gesamt", len(f))
c2.metric("Politiker", f["politician"].nunique())
c3.metric("Käufe", int((f["direction"] == "Kauf").sum()))
c4.metric("Verkäufe", int((f["direction"] == "Verkauf").sum()))

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📋 Alle Trades", "👤 Pro Politiker", "💼 Portfolio & Rendite",
     "🚨 Kaufsignal", "📈 Top-Aktien", "⏱️ Meldeverzug"]
)

# ────────────────────────────────────────────────────────────────────────────
# TAB 1: Alle Trades
# ────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Alle Transaktionen")
    show = f.sort_values("transaction_date", ascending=False).copy()
    show["transaction_date"] = show["transaction_date"].dt.date
    show["disclosure_date"]  = show["disclosure_date"].dt.date
    st.dataframe(
        show[["transaction_date", "politician", "chamber", "owner", "ticker",
              "asset", "direction", "amount_range", "disclosure_date", "source_url"]],
        use_container_width=True,
        column_config={
            "source_url":       st.column_config.LinkColumn("Quelle"),
            "transaction_date": "Transaktion",
            "disclosure_date":  "Offenlegung",
            "politician":       "Politiker",
            "chamber":          "Kammer",
            "owner":            "Inhaber",
            "ticker":           "Ticker",
            "asset":            "Wertpapier",
            "direction":        "Art",
            "amount_range":     "Betragsspanne",
        },
        hide_index=True,
    )
    st.download_button(
        "⬇️ Als CSV herunterladen",
        f.to_csv(index=False).encode("utf-8"),
        "politiker_trades.csv",
        "text/csv",
    )

# ────────────────────────────────────────────────────────────────────────────
# TAB 2: Pro Politiker
# ────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Aktivität pro Politiker")
    if not f.empty:
        agg = (f.groupby("politician")
                .agg(trades=("ticker", "count"),
                     volumen_mittel=("amount_mid", "sum"))
                .sort_values("trades", ascending=False))
        st.bar_chart(agg["trades"])
        agg["volumen_mittel"] = agg["volumen_mittel"].map(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "—")
        st.dataframe(agg, use_container_width=True)
    else:
        st.info("Keine Daten im aktuellen Filter.")


# ────────────────────────────────────────────────────────────────────────────
# TAB 3: Portfolio-Rangliste & historische Entwicklung
# ────────────────────────────────────────────────────────────────────────────
with tab3:
    import re as _re

    def clean_ticker_name(n):
        return _re.sub(r"\s*\(\d+\)\s*$", "", str(n)).strip()

    st.subheader("💼 Portfolio-Rangliste & historische Entwicklung")

    if not YFINANCE_OK:
        st.warning("⚠️ `pip install yfinance` ausführen — wird für alle Renditeberechnungen benötigt.")
        st.stop()

    # ── 1) Zeitraum-Filter ───────────────────────────────────────────────
    all_dates = df["transaction_date"].dropna()
    global_min = all_dates.min().date() if not all_dates.empty else dt.date(2016, 1, 1)
    global_max = dt.date.today()

    st.markdown("#### ⚙️ Analysezeitraum")
    rc1, rc2, rc3 = st.columns([2, 2, 1])
    with rc1:
        p_start = st.date_input("Von", value=dt.date(2020, 1, 1),
                                min_value=global_min, max_value=global_max,
                                key="port_start")
    with rc2:
        p_end = st.date_input("Bis", value=global_max,
                              min_value=global_min, max_value=global_max,
                              key="port_end")
    with rc3:
        st.markdown("<br>", unsafe_allow_html=True)
        recalc = st.button("🔄 Berechnen", key="calc_all", use_container_width=True)

    st.caption(
        "Rendite = Kursperformance gewichtet mit dem investierten Kapital je Position. "
        "Haltezeit: Erster Kauf bis letzter Verkauf (oder Periodenende bei offenen Positionen). "
        "Nur Positionen mit Überschneidung zum gewählten Zeitraum fließen ein."
    )
    st.markdown("---")

    # ── 2) Berechnung cachen ─────────────────────────────────────────────
    @st.cache_data(ttl=3600, show_spinner=False)
    def compute_all_portfolios(trades_hash: str, p_start_str: str, p_end_str: str):
        """
        Berechnet für alle Politiker:
        - Portfolio-Zusammensetzung (offene / geschlossene Positionen)
        - Volumengewichtete Gesamtrendite im Zeitraum
        - Tägliche Portfolio-Wertkurve (normiert auf 100)
        Gibt zurück: (ranking_df, history_dict {politiker: pd.Series})
        """
        p_start = pd.Timestamp(p_start_str)
        p_end   = pd.Timestamp(p_end_str)

        # Alle Trades mit Ticker und Datum
        td = df[
            df["ticker"].notna() & (df["ticker"] != "") &
            df["transaction_date"].notna()
        ].copy()

        politicians = td["politician"].dropna().unique()
        ranking_rows = []
        history_dict = {}

        for pol in politicians:
            pol_t = td[td["politician"] == pol].sort_values("transaction_date")
            tickers = pol_t["ticker"].unique()

            pos_rows = []
            for tk in tickers:
                tk_t  = pol_t[pol_t["ticker"] == tk]
                buys  = tk_t[tk_t["direction"] == "Kauf"]
                sells = tk_t[tk_t["direction"] == "Verkauf"]

                if buys.empty:
                    continue

                buy_vol  = buys["amount_mid"].sum()
                sell_vol = sells["amount_mid"].sum() if not sells.empty else 0
                n_buys, n_sells = len(buys), len(sells)
                is_open = (n_buys > n_sells) or (n_sells == 0)

                first_buy  = buys["transaction_date"].min()
                last_sell  = sells["transaction_date"].max() if not sells.empty else None

                asset_name = tk_t["asset"].mode()
                asset_name = clean_ticker_name(asset_name.iloc[0]) if not asset_name.empty else tk

                pos_rows.append({
                    "ticker":     tk,
                    "name":       asset_name,
                    "is_open":    is_open,
                    "buy_vol":    buy_vol if pd.notna(buy_vol) else 0,
                    "first_buy":  first_buy,
                    "last_sell":  last_sell,
                })

            if not pos_rows:
                continue

            # Rendite je Position im gewählten Zeitraum
            weighted_returns = []
            weights          = []
            daily_series     = {}  # tk -> pd.Series(index=dates, values=normalised price)

            for pos in pos_rows:
                tk         = pos["ticker"]
                inv        = pos["buy_vol"]
                hold_start = pos["first_buy"]
                hold_end   = pos["last_sell"] if not pos["is_open"] and pos["last_sell"] else p_end

                # Überschneidung Haltezeit ∩ Analysezeitraum
                eff_start = max(hold_start, p_start)
                eff_end   = min(hold_end,   p_end)
                if eff_start >= eff_end:
                    continue

                try:
                    ticker_obj = yf.Ticker(tk)
                    hist = ticker_obj.history(
                        start=eff_start.strftime("%Y-%m-%d"),
                        end=(eff_end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                        auto_adjust=True,
                    )
                    if hist.empty or len(hist) < 2:
                        continue

                    closes = hist["Close"].copy()
                    closes.index = pd.to_datetime(closes.index).tz_localize(None)

                    p0 = closes.iloc[0]
                    p1 = closes.iloc[-1]
                    ret = (p1 / p0 - 1) * 100

                    weighted_returns.append(ret * inv)
                    weights.append(inv)

                    # Normiert auf 100 für Portfolio-Kurve
                    daily_series[tk] = (closes / p0 * inv)  # gewichtete Kurve
                except Exception:
                    continue

            if not weights:
                continue

            total_weight  = sum(weights)
            weighted_ret  = sum(weighted_returns) / total_weight if total_weight else 0

            # Portfolio-Gesamtkurve: Summe der gewichteten Einzelkurven, normiert
            if daily_series:
                combined = pd.DataFrame(daily_series).fillna(method="ffill").fillna(method="bfill")
                portfolio_curve = combined.sum(axis=1)
                portfolio_curve = portfolio_curve / portfolio_curve.iloc[0] * 100
            else:
                portfolio_curve = pd.Series(dtype=float)

            n_open   = sum(1 for p in pos_rows if p["is_open"])
            n_closed = len(pos_rows) - n_open

            ranking_rows.append({
                "politician":    pol,
                "rendite_pct":   round(weighted_ret, 1),
                "positionen":    len(pos_rows),
                "offen":         n_open,
                "geschlossen":   n_closed,
                "invest_vol":    total_weight,
                "gewinn_ca":     total_weight * weighted_ret / 100,
            })
            history_dict[pol] = portfolio_curve

        ranking_df = pd.DataFrame(ranking_rows).sort_values(
            "rendite_pct", ascending=False
        ).reset_index(drop=True)
        ranking_df.index += 1  # Rang 1, 2, 3 …

        return ranking_df, history_dict

    # ── 3) Berechnung ausführen ───────────────────────────────────────────
    cache_key = f"{len(df)}_{df['transaction_date'].max()}"

    if "port_ranking" not in st.session_state or recalc:
        with st.spinner("Berechne Renditen für alle Politiker … (kann 1–2 Min. dauern)"):
            try:
                ranking_df, history_dict = compute_all_portfolios(
                    cache_key, str(p_start), str(p_end)
                )
                st.session_state["port_ranking"]  = ranking_df
                st.session_state["port_history"]  = history_dict
                st.session_state["port_period"]   = (p_start, p_end)
            except Exception as e:
                st.error(f"Fehler bei der Berechnung: {e}")
                st.stop()

    ranking_df   = st.session_state.get("port_ranking", pd.DataFrame())
    history_dict = st.session_state.get("port_history", {})
    cached_period= st.session_state.get("port_period", (p_start, p_end))

    if ranking_df.empty:
        st.info("Keine Renditen berechenbar. Prüfe ob yfinance installiert ist und Kursdaten verfügbar sind.")
    else:
        # ── 4) Gesamt-Kennzahlen ──────────────────────────────────────────
        best  = ranking_df.iloc[0]
        worst = ranking_df.iloc[-1]
        avg   = ranking_df["rendite_pct"].mean()

        km1, km2, km3, km4 = st.columns(4)
        km1.metric("Analysierte Politiker", len(ranking_df))
        km2.metric("Beste Rendite",
                   f"{best['rendite_pct']:+.1f}%", best["politician"])
        km3.metric("Schlechteste Rendite",
                   f"{worst['rendite_pct']:+.1f}%", worst["politician"])
        km4.metric("Ø Rendite alle",
                   f"{avg:+.1f}%")

        st.caption(
            f"Zeitraum: {cached_period[0].strftime('%d.%m.%Y')} – "
            f"{cached_period[1].strftime('%d.%m.%Y')}"
        )
        st.markdown("---")

        # ── 5) Rangliste ──────────────────────────────────────────────────
        st.markdown("#### 🏆 Rangliste (beste → schlechteste Rendite)")

        disp_rank = ranking_df.copy()
        disp_rank["rendite_pct"] = disp_rank["rendite_pct"].map(
            lambda x: f"{x:+.1f}%")
        disp_rank["invest_vol"] = disp_rank["invest_vol"].map(
            lambda x: f"${x:,.0f}" if x > 0 else "—")
        disp_rank["gewinn_ca"] = disp_rank["gewinn_ca"].map(
            lambda x: f"${x:+,.0f}" if pd.notna(x) else "—")

        st.dataframe(
            disp_rank[["politician", "rendite_pct", "invest_vol",
                        "gewinn_ca", "positionen", "offen", "geschlossen"]],
            use_container_width=True,
            column_config={
                "politician":  "Politiker",
                "rendite_pct": "Rendite (gewichtet)",
                "invest_vol":  "Invest. Kapital (ca.)",
                "gewinn_ca":   "Gewinn/Verlust (ca.)",
                "positionen":  "Positionen",
                "offen":       "Offen",
                "geschlossen": "Geschlossen",
            },
        )

        # ── 6) Rendite-Balkendiagramm alle Politiker ──────────────────────
        st.markdown("---")
        st.markdown("#### 📊 Rendite-Vergleich (alle Politiker)")
        chart_rank = ranking_df.set_index("politician")[["rendite_pct"]]
        chart_rank.columns = ["Rendite %"]
        st.bar_chart(chart_rank, color="#4f8ef7")

        # ── 7) Historische Portfolio-Kurven ───────────────────────────────
        st.markdown("---")
        st.markdown("#### 📈 Historische Portfolio-Entwicklung")
        st.caption("Normiert auf 100 = Startpunkt des gewählten Zeitraums. "
                   "Zeigt wie sich das Portfolio des Politikers entwickelt hätte "
                   "wenn man seine Positionen in den gemeldeten Gewichtungen gehalten hätte.")

        # Politiker-Auswahl für Kurvendiagramm
        top10 = ranking_df["politician"].head(10).tolist()
        avail = [p for p in ranking_df["politician"] if p in history_dict
                 and not history_dict[p].empty]
        sel_hist_pols = st.multiselect(
            "Politiker für Kurvendiagramm auswählen",
            options=avail,
            default=[p for p in top10 if p in avail][:5],
            key="hist_pol_sel",
        )

        if sel_hist_pols:
            curve_frames = {}
            for pol in sel_hist_pols:
                curve = history_dict.get(pol)
                if curve is not None and not curve.empty:
                    curve_frames[pol] = curve

            if curve_frames:
                curves_df = pd.DataFrame(curve_frames)
                # Gemeinsame Zeitachse: forward-fill fehlende Handelstage
                curves_df = curves_df.fillna(method="ffill").dropna(how="all")
                st.line_chart(curves_df, use_container_width=True)
                st.caption(
                    "Y-Achse = Portfolio-Wert indexiert (Start = 100). "
                    "Quelle: Yahoo Finance via yfinance. Keine Anlageberatung."
                )
            else:
                st.info("Keine Kursdaten für die gewählten Politiker verfügbar.")
        else:
            st.info("Wähle mindestens einen Politiker aus.")

        # ── 8) Einzelansicht Politiker ────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🔍 Einzelansicht: Portfolio eines Politikers")

        sel_detail_pol = st.selectbox(
            "Politiker auswählen",
            options=ranking_df["politician"].tolist(),
            key="detail_pol_sel",
        )

        detail_trades = df[
            (df["politician"] == sel_detail_pol) &
            df["ticker"].notna() & (df["ticker"] != "") &
            df["transaction_date"].notna()
        ].copy().sort_values("transaction_date")

        if not detail_trades.empty:
            detail_rows = []
            for tk in detail_trades["ticker"].unique():
                tk_t  = detail_trades[detail_trades["ticker"] == tk]
                buys  = tk_t[tk_t["direction"] == "Kauf"]
                sells = tk_t[tk_t["direction"] == "Verkauf"]
                if buys.empty:
                    continue
                buy_vol  = buys["amount_mid"].sum()
                sell_vol = sells["amount_mid"].sum() if not sells.empty else 0
                n_b, n_s = len(buys), len(sells)
                is_open  = (n_b > n_s) or (n_s == 0)
                first_b  = buys["transaction_date"].min()
                last_s   = sells["transaction_date"].max() if not sells.empty else None
                asset_n  = tk_t["asset"].mode()
                asset_n  = clean_ticker_name(asset_n.iloc[0]) if not asset_n.empty else tk

                # Rendite für diese Position im Zeitraum
                hold_end  = last_s if not is_open and last_s else pd.Timestamp(p_end)
                eff_start = max(first_b, pd.Timestamp(p_start))
                eff_end   = min(hold_end, pd.Timestamp(p_end))
                rendite   = None
                k_start_p = None
                k_end_p   = None
                if eff_start < eff_end:
                    try:
                        h = yf.Ticker(tk).history(
                            start=eff_start.strftime("%Y-%m-%d"),
                            end=(eff_end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                            auto_adjust=True,
                        )
                        if not h.empty and len(h) >= 2:
                            k_start_p = round(h["Close"].iloc[0], 2)
                            k_end_p   = round(h["Close"].iloc[-1], 2)
                            rendite   = round((k_end_p / k_start_p - 1) * 100, 1)
                    except Exception:
                        pass

                detail_rows.append({
                    "logo":        logo_url(tk) or "",
                    "ticker":      tk,
                    "unternehmen": asset_n,
                    "status":      "Offen ✅" if is_open else "Geschlossen ❌",
                    "n_kaeufe":    n_b,
                    "n_verkaeufe": n_s,
                    "kauf_vol":    buy_vol if pd.notna(buy_vol) else 0,
                    "sell_vol":    sell_vol,
                    "erster_kauf": first_b.date() if pd.notna(first_b) else None,
                    "letzter_sell":last_s.date() if last_s and pd.notna(last_s) else None,
                    "kurs_start":  f"${k_start_p:.2f}" if k_start_p else "—",
                    "kurs_end":    f"${k_end_p:.2f}"   if k_end_p   else "—",
                    "rendite_pct": rendite,
                    "gewinn_ca":   (buy_vol * rendite / 100)
                                   if rendite and buy_vol else None,
                })

            if detail_rows:
                det_df = pd.DataFrame(detail_rows).sort_values(
                    "rendite_pct", ascending=False, na_position="last")

                # Gesamt-Metriken
                with_ret = det_df.dropna(subset=["rendite_pct"])
                if not with_ret.empty:
                    total_inv = with_ret["kauf_vol"].sum()
                    w_ret = ((with_ret["rendite_pct"] * with_ret["kauf_vol"]).sum()
                             / total_inv) if total_inv else 0
                    g_sum = with_ret["gewinn_ca"].sum()
                    dm1, dm2, dm3 = st.columns(3)
                    dm1.metric("Portfolio-Rendite (gewichtet)", f"{w_ret:+.1f}%")
                    dm2.metric("Investiertes Kapital (ca.)", f"${total_inv:,.0f}")
                    dm3.metric("Geschätzter Gewinn/Verlust", f"${g_sum:+,.0f}")

                disp_det = det_df.copy()
                disp_det["kauf_vol"]   = disp_det["kauf_vol"].map(
                    lambda x: f"${x:,.0f}" if x > 0 else "—")
                disp_det["sell_vol"]   = disp_det["sell_vol"].map(
                    lambda x: f"${x:,.0f}" if x > 0 else "—")
                disp_det["rendite_pct"] = disp_det["rendite_pct"].map(
                    lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
                disp_det["gewinn_ca"]  = disp_det["gewinn_ca"].map(
                    lambda x: f"${x:+,.0f}" if pd.notna(x) else "—")

                st.dataframe(
                    disp_det[["logo","ticker","unternehmen","status",
                               "n_kaeufe","n_verkaeufe","kauf_vol","sell_vol",
                               "erster_kauf","letzter_sell",
                               "kurs_start","kurs_end","rendite_pct","gewinn_ca"]],
                    use_container_width=True,
                    column_config={
                        "logo":        st.column_config.ImageColumn("", width="small"),
                        "ticker":      "Ticker",
                        "unternehmen": "Unternehmen",
                        "status":      "Status",
                        "n_kaeufe":    "Käufe",
                        "n_verkaeufe": "Verkäufe",
                        "kauf_vol":    "Kaufvol. (ca.)",
                        "sell_vol":    "Verkaufvol. (ca.)",
                        "erster_kauf": "Erster Kauf",
                        "letzter_sell":"Letzter Verkauf",
                        "kurs_start":  "Kurs Start",
                        "kurs_end":    "Kurs Ende",
                        "rendite_pct": "Rendite",
                        "gewinn_ca":   "Gewinn/Verlust (ca.)",
                    },
                    hide_index=True,
                )
                st.caption(
                    "⚠️ Rendite = Kursperformance im Analysezeitraum. "
                    "Kapital = Mittelpunkt der gemeldeten Betragsspanne. "
                    "Keine Anlageberatung."
                )

# ────────────────────────────────────────────────────────────────────────────
# TAB 4: Kaufsignal — Aktien mit ungewöhnlich hoher Kaufaktivität
# ────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("🚨 Kaufsignal — Aktien mit ungewöhnlich hoher Kaufaktivität")
    st.caption(
        "Erkennt Aktien, bei denen Kongressmitglieder innerhalb kurzer Zeit "
        "überdurchschnittlich oft und von mehreren Seiten kaufen — ein klassisches "
        "Insidersignal. Score berücksichtigt: Anzahl Käufe, Kaufvolumen, "
        "Anzahl verschiedener Politiker und Beschleunigung (mehr Käufe als im Vorraum)."
    )

    # ── Einstellungen ─────────────────────────────────────────────────────
    sg1, sg2, sg3 = st.columns(3)
    with sg1:
        signal_days = st.selectbox(
            "⏱️ Beobachtungsfenster",
            [7, 14, 21, 30, 60, 90],
            index=2,   # 21 Tage default
            key="signal_days",
            help="Wie viele Tage zurück werden auf erhöhte Kaufaktivität geprüft?",
        )
    with sg2:
        signal_top_n = st.selectbox(
            "Anzahl Signale",
            [5, 10, 15, 20], index=1, key="signal_top_n",
        )
    with sg3:
        min_politicians = st.selectbox(
            "Min. Politiker (Diversität)",
            [1, 2, 3, 4], index=1, key="signal_min_pol",
            help="Mindestens N verschiedene Politiker müssen gekauft haben.",
        )

    st.markdown("---")

    # ── Score-Berechnung ──────────────────────────────────────────────────
    buys_all = df[
        (df["direction"] == "Kauf") &
        df["ticker"].notna() & (df["ticker"] != "") &
        df["transaction_date"].notna()
    ].copy()

    if buys_all.empty:
        st.info("Keine Kaufdaten vorhanden.")
    else:
        today_ts     = pd.Timestamp.today().normalize()
        window_start = today_ts - pd.Timedelta(days=signal_days)
        # Vergleichsfenster: gleiche Länge davor (für Beschleunigungsmessung)
        prev_start   = window_start - pd.Timedelta(days=signal_days)

        recent = buys_all[buys_all["transaction_date"] >= window_start]
        prev   = buys_all[
            (buys_all["transaction_date"] >= prev_start) &
            (buys_all["transaction_date"] <  window_start)
        ]

        if recent.empty:
            # Kein echtes "heute" in Demo-Daten → relativen Anker nehmen
            anchor      = buys_all["transaction_date"].max()
            window_start= anchor - pd.Timedelta(days=signal_days)
            prev_start  = window_start - pd.Timedelta(days=signal_days)
            recent = buys_all[buys_all["transaction_date"] >= window_start]
            prev   = buys_all[
                (buys_all["transaction_date"] >= prev_start) &
                (buys_all["transaction_date"] <  window_start)
            ]
            st.caption(
                f"ℹ️ Demo-Modus: Anker = letzter Trade ({anchor.date()}). "
                f"Fenster: {window_start.date()} – {anchor.date()}"
            )
        else:
            st.caption(
                f"Fenster: {window_start.date()} – {today_ts.date()} "
                f"({signal_days} Tage) · {len(recent)} Käufe im Fenster"
            )

        # Aggregation im aktuellen Fenster
        agg_recent = (
            recent.groupby("ticker")
            .agg(
                n_buys    =("politician", "count"),
                n_pols    =("politician", "nunique"),
                buy_vol   =("amount_mid", "sum"),
                last_buy  =("transaction_date", "max"),
            )
            .reset_index()
        )
        agg_recent = agg_recent[agg_recent["n_pols"] >= min_politicians]

        # Aggregation im Vorvergleichsfenster
        agg_prev = (
            prev.groupby("ticker")
            .agg(n_buys_prev=("politician", "count"))
            .reset_index()
        )

        sig = agg_recent.merge(agg_prev, on="ticker", how="left")
        sig["n_buys_prev"] = sig["n_buys_prev"].fillna(0)

        # Beschleunigung: wie viel mehr Käufe als im Vorraum (mind. 0)
        sig["beschleunigung"] = (sig["n_buys"] - sig["n_buys_prev"]).clip(lower=0)

        # Normierung auf 0–1 für Score-Komponenten
        def norm(s):
            mn, mx = s.min(), s.max()
            return (s - mn) / (mx - mn + 1e-9)

        sig["score"] = (
            norm(sig["n_buys"])        * 0.30 +
            norm(sig["n_pols"])        * 0.30 +
            norm(sig["buy_vol"])       * 0.20 +
            norm(sig["beschleunigung"])* 0.20
        ) * 100

        sig = sig.sort_values("score", ascending=False).head(signal_top_n).reset_index(drop=True)

        # Unternehmensnamen aus Gesamtdaten holen
        nm_src = df[df["ticker"].notna() & df["asset"].notna()]
        def best_name(tk):
            hits = nm_src[nm_src["ticker"] == tk]["asset"]
            if hits.empty: return tk
            import re as _re2
            return _re2.sub(r"\s*\(\d+\)\s*$", "", hits.mode()[0]).strip()

        sig["unternehmen"] = sig["ticker"].map(best_name)
        sig["last_buy"]    = sig["last_buy"].dt.date

        if sig.empty:
            st.info(f"Keine Aktien mit ≥ {min_politicians} verschiedenen Käufern im Fenster.")
        else:
            # ── Signal-Karten ─────────────────────────────────────────────
            st.markdown(f"#### 🔥 Top {len(sig)} Kaufsignale")

            # Score-Balken + Info je Aktie
            for rank, row in sig.iterrows():
                logo_tag = logo_url(row["ticker"])
                col_logo, col_info, col_bar, col_nums = st.columns([0.4, 2.5, 3, 2])

                with col_logo:
                    if logo_tag:
                        st.image(logo_tag, width=32)

                with col_info:
                    st.markdown(
                        f"**{row['ticker']}**  \n"
                        f"<span style='font-size:0.78rem;opacity:0.65'>"
                        f"{row['unternehmen']}</span>",
                        unsafe_allow_html=True,
                    )

                with col_bar:
                    score = row["score"]
                    color = (
                        "#22c55e" if score >= 66 else
                        "#f59e0b" if score >= 33 else
                        "#94a3b8"
                    )
                    label = (
                        "🔥 Stark" if score >= 66 else
                        "📈 Mittel" if score >= 33 else
                        "👀 Schwach"
                    )
                    st.markdown(
                        f"<div style='margin-top:6px'>"
                        f"<div style='display:flex;align-items:center;gap:8px'>"
                        f"<div style='flex:1;height:10px;border-radius:5px;"
                        f"background:#2d3348'>"
                        f"<div style='width:{score:.0f}%;height:100%;"
                        f"border-radius:5px;background:{color}'></div></div>"
                        f"<span style='font-size:0.75rem;color:{color};min-width:70px'>"
                        f"{label} ({score:.0f})</span>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

                with col_nums:
                    accel = row["beschleunigung"]
                    accel_str = f"+{accel:.0f} ↑" if accel > 0 else "—"
                    st.markdown(
                        f"<div style='font-size:0.78rem;margin-top:4px;line-height:1.6'>"
                        f"🛒 <b>{row['n_buys']:.0f}</b> Käufe &nbsp;"
                        f"👥 <b>{row['n_pols']:.0f}</b> Politiker<br>"
                        f"💰 <b>${row['buy_vol']:,.0f}</b> &nbsp;"
                        f"⚡ Beschl.: <b>{accel_str}</b>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                st.divider()

            # ── Kurs + Kauf-Zeitpunkte (Chart) ───────────────────────────
            st.markdown("---")
            st.markdown("#### 📉 Kursverlauf + Kaufzeitpunkte")
            st.caption(
                "Zeigt den Kursverlauf der Signal-Aktien. "
                "Die Käufe der Politiker fallen in den grau markierten Bereich (Beobachtungsfenster)."
            )

            if not YFINANCE_OK:
                st.warning("⚠️ `pip install yfinance` für Kurshistorie benötigt.")
            else:
                chart_tickers = sig["ticker"].tolist()
                chart_labels  = [
                    f"{t} – {sig.loc[sig['ticker']==t,'unternehmen'].iloc[0]}"
                    for t in chart_tickers
                ]
                label_map = dict(zip(chart_labels, chart_tickers))

                sel_signal_chart = st.multiselect(
                    "Aktien für Chart auswählen",
                    chart_labels,
                    default=chart_labels[:min(3, len(chart_labels))],
                    key="signal_chart_sel",
                )
                chart_period_map = {
                    "3 Monate": "3mo", "6 Monate": "6mo",
                    "1 Jahr": "1y",    "2 Jahre": "2y",
                }
                chart_period = st.selectbox(
                    "Kurszeitraum", list(chart_period_map.keys()),
                    index=0, key="signal_chart_period",
                )

                if sel_signal_chart:
                    with st.spinner("Lade Kursdaten …"):
                        price_frames = {}
                        for lbl in sel_signal_chart:
                            tk = label_map[lbl]
                            hist = fetch_price_history(tk, chart_period_map[chart_period])
                            if not hist.empty:
                                price_frames[tk] = hist["Kurs (USD)"]

                    if price_frames:
                        chart_df = pd.DataFrame(price_frames)
                        # Normiert auf 100 für Vergleich
                        chart_df = chart_df / chart_df.iloc[0] * 100
                        st.line_chart(chart_df, use_container_width=True)
                        st.caption(
                            f"Normiert (Start = 100) · {chart_period} · "
                            "Yahoo Finance via yfinance · Keine Anlageberatung."
                        )

            # ── Detail-Tabelle ────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 📊 Detailtabelle Kaufsignale")
            disp_sig = sig.copy()
            disp_sig["logo"]     = disp_sig["ticker"].map(lambda t: logo_url(t) or "")
            disp_sig["score"]    = disp_sig["score"].map(lambda x: f"{x:.0f}/100")
            disp_sig["buy_vol"]  = disp_sig["buy_vol"].map(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—")
            disp_sig["beschleunigung"] = disp_sig["beschleunigung"].map(
                lambda x: f"+{x:.0f}" if x > 0 else "—")

            st.dataframe(
                disp_sig[["logo", "ticker", "unternehmen", "score",
                           "n_buys", "n_pols", "buy_vol",
                           "beschleunigung", "last_buy"]],
                use_container_width=True,
                column_config={
                    "logo":            st.column_config.ImageColumn("", width="small"),
                    "ticker":          "Ticker",
                    "unternehmen":     "Unternehmen",
                    "score":           "Signal-Score",
                    "n_buys":          "Käufe im Fenster",
                    "n_pols":          "Versch. Politiker",
                    "buy_vol":         "Kaufvolumen (ca.)",
                    "beschleunigung":  "Beschleunigung ↑",
                    "last_buy":        "Letzter Kauf",
                },
                hide_index=True,
            )

# ────────────────────────────────────────────────────────────────────────────
# TAB 5: Top-Aktien (erweitert)
# ────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Meistgehandelte Aktien")

    if not f.empty:
        # ── 1) Zeitraum-Filter speziell für Top-Aktien ─────────────────────
        col_tl, col_tr = st.columns([2, 1])
        with col_tl:
            valid_top = df["transaction_date"].dropna()  # immer alle Daten als Basis
            if not valid_top.empty:
                top_min = valid_top.min().date()
                top_max = valid_top.max().date()
                top_range = st.date_input(
                    "📅 Betrachtungszeitraum (Top-Aktien)",
                    value=(top_min, top_max),
                    min_value=top_min,
                    max_value=top_max,
                    key="top_stocks_range",
                )
            else:
                top_range = None

        with col_tr:
            top_n = st.selectbox("Anzahl Top-Aktien", [10, 20, 30, 50], index=0)

        # Zeitraum-Filter: erst anwenden wenn zwei Daten gewählt wurden
        f_top = df.copy()  # immer vom ungefilterten Datensatz starten
        if (top_range and isinstance(top_range, tuple) and len(top_range) == 2
                and top_range[0] is not None and top_range[1] is not None):
            ts, te = top_range
            f_top = f_top[(f_top["transaction_date"].dt.date >= ts) &
                          (f_top["transaction_date"].dt.date <= te)]
            st.caption(f"📅 Gefiltert: {ts.strftime('%d.%m.%Y')} – {te.strftime('%d.%m.%Y')} · {len(f_top):,} Trades")
        elif top_range and not isinstance(top_range, tuple):
            # Nur ein Datum gewählt → noch kein Filter, Hinweis zeigen
            st.caption("⬆️ Bitte auch ein Enddatum auswählen.")
            f_top = df.copy()

        f_top = f_top[f_top["ticker"].notna() & (f_top["ticker"] != "")]

        if f_top.empty:
            st.info("Keine Daten im gewählten Zeitraum.")
        else:
            # ── 2) Name-Map: Ticker → bereinigter Unternehmensname ──────────
            # Nimmt den häufigsten asset-Wert pro Ticker (entfernt " (1)", " (2)" etc.)
            import re as _re
            def clean_name(n: str) -> str:
                return _re.sub(r"\s*\(\d+\)\s*$", "", str(n)).strip()

            name_map: dict[str, str] = {}
            if "asset" in f_top.columns:
                nm = (f_top[f_top["ticker"].notna() & f_top["asset"].notna()]
                      .groupby("ticker")["asset"]
                      .agg(lambda s: s.mode()[0] if not s.mode().empty else s.iloc[0]))
                name_map = {tk: clean_name(nm_val) for tk, nm_val in nm.items()}

            # ── 3) Aggregation mit Volumen ──────────────────────────────────
            top = (f_top.groupby("ticker")
                   .agg(
                       trades      =("politician", "count"),
                       kaeufe      =("direction", lambda s: (s == "Kauf").sum()),
                       verkaeufe   =("direction", lambda s: (s == "Verkauf").sum()),
                       kauf_vol    =("amount_mid", lambda s:
                                     s[f_top.loc[s.index, "direction"] == "Kauf"].sum()),
                       verkauf_vol =("amount_mid", lambda s:
                                     s[f_top.loc[s.index, "direction"] == "Verkauf"].sum()),
                   )
                   .sort_values("trades", ascending=False)
                   .head(top_n)
                   .reset_index())

            top["unternehmen"] = top["ticker"].map(lambda t: name_map.get(t, t))
            top["gesamt_vol"]  = top["kauf_vol"] + top["verkauf_vol"]
            top["buy_pct"]     = top.apply(
                lambda r: r["kauf_vol"] / r["gesamt_vol"] * 100
                if r["gesamt_vol"] > 0 else 0, axis=1
            )

            # ── 4) Balkendiagramm Käufe vs. Verkäufe ───────────────────────
            st.markdown("#### Käufe vs. Verkäufe (Anzahl Trades)")
            chart_data = top.set_index("ticker")[["kaeufe", "verkaeufe"]]
            chart_data.columns = ["Käufe", "Verkäufe"]
            st.bar_chart(chart_data, color=["#22c55e", "#ef4444"])

            # ── 5) Kaufdruck-Indikator ──────────────────────────────────────
            st.markdown("---")
            render_buy_pressure(top, name_map=name_map)

            # ── 6) Tabelle mit Logo, Name & Volumen ────────────────────────
            st.markdown("---")
            st.markdown("#### 📊 Detailtabelle")

            # Logo-Spalte als HTML
            display_top = top.copy()
            display_top["logo"] = display_top["ticker"].map(
                lambda t: logo_url(t) or ""
            )
            display_top["kauf_vol"]    = display_top["kauf_vol"].map(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—")
            display_top["verkauf_vol"] = display_top["verkauf_vol"].map(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—")
            display_top["gesamt_vol"]  = display_top["gesamt_vol"].map(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "—")
            display_top["buy_pct"]     = display_top["buy_pct"].map(
                lambda x: f"{x:.0f}%")

            st.dataframe(
                display_top[["logo", "ticker", "unternehmen", "trades",
                             "kaeufe", "verkaeufe",
                             "kauf_vol", "verkauf_vol", "gesamt_vol", "buy_pct"]],
                use_container_width=True,
                column_config={
                    "logo":        st.column_config.ImageColumn("", width="small"),
                    "ticker":      "Ticker",
                    "unternehmen": "Unternehmen",
                    "trades":      "Trades gesamt",
                    "kaeufe":      "Käufe (Anzahl)",
                    "verkaeufe":   "Verkäufe (Anzahl)",
                    "kauf_vol":    "Kaufvolumen (ca.)",
                    "verkauf_vol": "Verkaufsvolumen (ca.)",
                    "gesamt_vol":  "Gesamtvolumen (ca.)",
                    "buy_pct":     "Kaufanteil %",
                },
                hide_index=True,
            )

            # ── 6) Kurshistorie ─────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 📉 Kurshistorie")

            if not YFINANCE_OK:
                st.warning(
                    "⚠️ **yfinance nicht installiert.** "
                    "Bitte `pip install yfinance` ausführen, um Kurshistorien zu laden."
                )
            else:
                col_kl, col_kr = st.columns([1, 2])
                with col_kl:
                    period_map = {
                        "3 Monate": "3mo",
                        "6 Monate": "6mo",
                        "1 Jahr":   "1y",
                        "2 Jahre":  "2y",
                        "5 Jahre":  "5y",
                    }
                    period_label = st.selectbox(
                        "Kurszeitraum", list(period_map.keys()),
                        index=4, key="price_period"
                    )
                    price_period = period_map[period_label]

                with col_kr:
                    ticker_choices = top["ticker"].tolist()
                    ticker_labels  = [
                        f"{t} – {name_map.get(t, t)}" for t in ticker_choices
                    ]
                    label_to_ticker = dict(zip(ticker_labels, ticker_choices))
                    sel_labels = st.multiselect(
                        "Aktien auswählen",
                        ticker_labels,
                        default=ticker_labels[:min(5, len(ticker_labels))],
                        key="price_tickers",
                    )
                    sel_price_tickers = [label_to_ticker[l] for l in sel_labels]

                if sel_price_tickers:
                    with st.spinner("Lade Kursdaten …"):
                        price_frames = {}
                        for tk in sel_price_tickers:
                            hist = fetch_price_history(tk, price_period)
                            if not hist.empty:
                                price_frames[tk] = hist["Kurs (USD)"]
                            else:
                                st.caption(f"⚠️ Keine Kursdaten für {tk}")

                    if price_frames:
                        combined = pd.DataFrame(price_frames)
                        # Normiert auf 100 für bessere Vergleichbarkeit
                        norm_toggle = st.checkbox(
                            "Auf 100 normieren (relativer Vergleich)",
                            value=True, key="normalize_prices"
                        )
                        if norm_toggle:
                            combined = combined / combined.iloc[0] * 100
                            y_label = "Indexiert (Start = 100)"
                        else:
                            y_label = "Kurs (USD)"

                        st.line_chart(combined, use_container_width=True)
                        st.caption(
                            f"Quelle: Yahoo Finance via yfinance · {period_label} · "
                            f"{'Normiert auf 100 = Startpunkt' if norm_toggle else 'Absoluter Kurs in USD'}"
                        )
                    else:
                        st.info("Keine Kursdaten für die gewählten Ticker verfügbar.")
                else:
                    st.info("Wähle mindestens eine Aktie aus der Liste oben.")
    else:
        st.info("Keine Daten im aktuellen Filter.")

# ────────────────────────────────────────────────────────────────────────────
# TAB 6: Meldeverzug
# ────────────────────────────────────────────────────────────────────────────
with tab6:
    st.subheader("Meldeverzug (Tage zwischen Transaktion und Offenlegung)")
    st.caption("STOCK Act schreibt eine Offenlegung innerhalb von 45 Tagen vor.")
    g = f.dropna(subset=["transaction_date", "disclosure_date"]).copy()
    if not g.empty:
        g["verzug_tage"] = (g["disclosure_date"] - g["transaction_date"]).dt.days
        late = g[g["verzug_tage"] > 45]
        cc1, cc2 = st.columns(2)
        cc1.metric("Ø Verzug (Tage)", f"{g['verzug_tage'].mean():.0f}")
        cc2.metric("Verspätet (>45 Tage)", len(late))
        st.dataframe(
            g[["politician", "ticker", "transaction_date",
               "disclosure_date", "verzug_tage"]]
            .sort_values("verzug_tage", ascending=False),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Keine ausreichenden Datumsangaben.")

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "⚠️ Hinweis: Beträge sind gesetzlich nur als Spannen verfügbar. "
    "Diese Anwendung dient der Transparenz und ist keine Anlageberatung. "
    "Jede Zeile verlinkt auf die Originaloffenlegung. "
    "Kurshistorie via Yahoo Finance (yfinance)."
)
