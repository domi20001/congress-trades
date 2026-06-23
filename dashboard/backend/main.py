"""
Backend API – US Politiker Aktien Dashboard
============================================
FastAPI-Server der PostgreSQL (Supabase) liest und JSON-Endpunkte liefert.

Start:  uvicorn main:app --reload --port 8000
"""

import os, hashlib, datetime as dt, math, re
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

app = FastAPI(title="Politiker Trades API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Datenbankverbindung ───────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    return create_engine(DATABASE_URL)

def get_df() -> pd.DataFrame:
    try:
        engine = get_engine()
        with engine.connect() as con:
            df = pd.read_sql_query(text("SELECT * FROM trades"), con)
        for c in ["transaction_date", "disclosure_date"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")
        df["amount_mid"] = pd.to_numeric(df.get("amount_mid"), errors="coerce")
        return df
    except Exception as e:
        print(f"DB Fehler: {e}")
        return pd.DataFrame()

def clean(n: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", str(n)).strip()

@app.get("/api/debug")
def debug():
    try:
        engine = get_engine()
        with engine.connect() as con:
            result = con.execute(text("SELECT COUNT(*) FROM trades"))
            count = result.fetchone()[0]
        return {"status": "ok", "count": count, "db_url_set": bool(DATABASE_URL)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ── /api/summary ─────────────────────────────────────────────────────────
@app.get("/api/summary")
def summary():
    df = get_df()
    if df.empty:
        return {"total": 0, "politicians": 0, "buys": 0, "sells": 0,
                "latest_date": None, "tickers": 0}
    return {
        "total":       int(len(df)),
        "politicians": int(df["politician"].nunique()),
        "buys":        int((df["direction"] == "Kauf").sum()),
        "sells":       int((df["direction"] == "Verkauf").sum()),
        "latest_date": str(df["transaction_date"].max().date()),
        "tickers":     int(df["ticker"].dropna().nunique()),
    }


# ── /api/trades ──────────────────────────────────────────────────────────
@app.get("/api/trades")
def trades(
    politician: Optional[str] = None,
    ticker:     Optional[str] = None,
    direction:  Optional[str] = None,
    chamber:    Optional[str] = None,
    date_from:  Optional[str] = None,
    date_to:    Optional[str] = None,
    limit:      int = 200,
    offset:     int = 0,
):
    df = get_df()
    if df.empty:
        return {"trades": [], "total": 0}
    if politician:
        df = df[df["politician"].str.contains(politician, case=False, na=False)]
    if ticker:
        df = df[df["ticker"].str.upper() == ticker.upper()]
    if direction:
        df = df[df["direction"] == direction]
    if chamber:
        df = df[df["chamber"] == chamber]
    if date_from:
        df = df[df["transaction_date"] >= pd.Timestamp(date_from)]
    if date_to:
        df = df[df["transaction_date"] <= pd.Timestamp(date_to)]

    df = df.sort_values("transaction_date", ascending=False)
    total = len(df)
    page  = df.iloc[offset : offset + limit]

    records = []
    for _, r in page.iterrows():
        records.append({
            "politician":       r.get("politician"),
            "chamber":          r.get("chamber"),
            "ticker":           r.get("ticker"),
            "asset":            r.get("asset"),
            "direction":        r.get("direction"),
            "amount_range":     r.get("amount_range"),
            "amount_mid":       None if pd.isna(r.get("amount_mid")) else float(r["amount_mid"]),
            "transaction_date": str(r["transaction_date"].date()) if pd.notna(r.get("transaction_date")) else None,
            "disclosure_date":  str(r["disclosure_date"].date())  if pd.notna(r.get("disclosure_date")) else None,
            "source_url":       r.get("source_url"),
        })
    return {"trades": records, "total": total}


# ── /api/politicians ──────────────────────────────────────────────────────
@app.get("/api/politicians")
def politicians():
    df = get_df()
    if df.empty:
        return []
    agg = (df.groupby("politician")
             .agg(trades=("ticker","count"),
                  buy_vol=("amount_mid", lambda s: s[df.loc[s.index,"direction"]=="Kauf"].sum()),
                  buys=("direction", lambda s: (s=="Kauf").sum()),
                  sells=("direction", lambda s: (s=="Verkauf").sum()),
                  last_trade=("transaction_date","max"),
                  chamber=("chamber", lambda s: s.mode()[0] if not s.mode().empty else ""),
             )
             .sort_values("trades", ascending=False)
             .reset_index())
    result = []
    for _, r in agg.iterrows():
        result.append({
            "name":       r["politician"],
            "chamber":    r["chamber"],
            "trades":     int(r["trades"]),
            "buys":       int(r["buys"]),
            "sells":      int(r["sells"]),
            "buy_vol":    0 if math.isnan(r["buy_vol"]) else float(r["buy_vol"]),
            "last_trade": str(r["last_trade"].date()) if pd.notna(r["last_trade"]) else None,
        })
    return result


# ── /api/top_stocks ───────────────────────────────────────────────────────
@app.get("/api/top_stocks")
def top_stocks(
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    limit:     int = 20,
):
    df = get_df()
    if df.empty:
        return []
    d = df[df["ticker"].notna() & (df["ticker"] != "")].copy()
    if date_from:
        d = d[d["transaction_date"] >= pd.Timestamp(date_from)]
    if date_to:
        d = d[d["transaction_date"] <= pd.Timestamp(date_to)]
    if d.empty:
        return []

    agg = (d.groupby("ticker")
            .agg(
                trades      =("politician","count"),
                n_pols      =("politician","nunique"),
                kaeufe      =("direction", lambda s: (s=="Kauf").sum()),
                verkaeufe   =("direction", lambda s: (s=="Verkauf").sum()),
                kauf_vol    =("amount_mid", lambda s: s[d.loc[s.index,"direction"]=="Kauf"].sum()),
                verkauf_vol =("amount_mid", lambda s: s[d.loc[s.index,"direction"]=="Verkauf"].sum()),
                asset       =("asset", lambda s: clean(s.mode()[0]) if not s.mode().empty else ""),
            )
            .sort_values("trades", ascending=False)
            .head(limit)
            .reset_index())

    result = []
    for _, r in agg.iterrows():
        kv = float(r["kauf_vol"]) if not math.isnan(float(r["kauf_vol"])) else 0
        vv = float(r["verkauf_vol"]) if not math.isnan(float(r["verkauf_vol"])) else 0
        tot = kv + vv
        result.append({
            "ticker":      r["ticker"],
            "name":        r["asset"],
            "trades":      int(r["trades"]),
            "n_pols":      int(r["n_pols"]),
            "buys":        int(r["kaeufe"]),
            "sells":       int(r["verkaeufe"]),
            "buy_vol":     kv,
            "sell_vol":    vv,
            "total_vol":   tot,
            "buy_pct":     round(kv / tot * 100, 1) if tot > 0 else 0,
        })
    return result


# ── /api/signals ──────────────────────────────────────────────────────────
@app.get("/api/signals")
def signals(days: int = 21, min_pols: int = 2, limit: int = 10):
    df = get_df()
    if df.empty:
        return []

    buys = df[(df["direction"] == "Kauf") & df["ticker"].notna() & (df["ticker"] != "")].copy()
    if buys.empty:
        return []

    today        = pd.Timestamp.today().normalize()
    window_start = today - pd.Timedelta(days=days)
    prev_start   = window_start - pd.Timedelta(days=days)

    recent = buys[buys["transaction_date"] >= window_start]
    if recent.empty:
        anchor       = buys["transaction_date"].max()
        window_start = anchor - pd.Timedelta(days=days)
        prev_start   = window_start - pd.Timedelta(days=days)
        recent       = buys[buys["transaction_date"] >= window_start]

    prev = buys[(buys["transaction_date"] >= prev_start) &
                (buys["transaction_date"] <  window_start)]

    agg_r = (recent.groupby("ticker")
              .agg(n_buys=("politician","count"),
                   n_pols=("politician","nunique"),
                   buy_vol=("amount_mid","sum"),
                   last_buy=("transaction_date","max"),
                   asset=("asset", lambda s: clean(s.mode()[0]) if not s.mode().empty else ""))
              .reset_index())
    agg_r = agg_r[agg_r["n_pols"] >= min_pols]
    if agg_r.empty:
        return []

    agg_p = (prev.groupby("ticker")
              .agg(n_buys_prev=("politician","count"))
              .reset_index())

    sig = agg_r.merge(agg_p, on="ticker", how="left")
    sig["n_buys_prev"] = sig["n_buys_prev"].fillna(0)
    sig["accel"]       = (sig["n_buys"] - sig["n_buys_prev"]).clip(lower=0)

    def norm(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn + 1e-9)

    sig["score"] = (
        norm(sig["n_buys"]) * 0.30 +
        norm(sig["n_pols"]) * 0.30 +
        norm(sig["buy_vol"])* 0.20 +
        norm(sig["accel"])  * 0.20
    ) * 100

    sig = sig.sort_values("score", ascending=False).head(limit).reset_index(drop=True)
    result = []
    for _, r in sig.iterrows():
        bv = float(r["buy_vol"]) if not math.isnan(float(r["buy_vol"])) else 0
        result.append({
            "ticker":   r["ticker"],
            "name":     r["asset"],
            "score":    round(float(r["score"]), 1),
            "n_buys":   int(r["n_buys"]),
            "n_pols":   int(r["n_pols"]),
            "buy_vol":  bv,
            "accel":    int(r["accel"]),
            "last_buy": str(r["last_buy"].date()) if pd.notna(r["last_buy"]) else None,
            "label":    "stark" if r["score"] >= 66 else "mittel" if r["score"] >= 33 else "schwach",
        })
    return result


# ── /api/price_history ────────────────────────────────────────────────────
@app.get("/api/price_history/{ticker}")
def price_history(ticker: str, period: str = "1y"):
    if not YF_OK:
        return {"error": "yfinance not installed"}
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if hist.empty:
            return []
        hist.index = pd.to_datetime(hist.index).tz_localize(None)
        return [
            {"date": str(d.date()), "close": round(float(c), 2)}
            for d, c in zip(hist.index, hist["Close"])
        ]
    except Exception as e:
        return {"error": str(e)}


# ── /api/portfolio/{politician} ────────────────────────────────────────────
@app.get("/api/portfolio/{politician}")
def portfolio(politician: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    df = get_df()
    if df.empty:
        return {"positions": []}

    pol = df[
        (df["politician"] == politician) &
        df["ticker"].notna() & (df["ticker"] != "") &
        df["transaction_date"].notna()
    ].copy().sort_values("transaction_date")

    if pol.empty:
        return {"positions": []}

    p_start = pd.Timestamp(date_from) if date_from else pol["transaction_date"].min()
    p_end   = pd.Timestamp(date_to)   if date_to   else pd.Timestamp.today()

    positions = []
    for tk in pol["ticker"].unique():
        tk_t  = pol[pol["ticker"] == tk]
        buys  = tk_t[tk_t["direction"] == "Kauf"]
        sells = tk_t[tk_t["direction"] == "Verkauf"]
        if buys.empty:
            continue
        bv = float(buys["amount_mid"].sum()) if not math.isnan(float(buys["amount_mid"].sum())) else 0
        sv = float(sells["amount_mid"].sum()) if not sells.empty and not math.isnan(float(sells["amount_mid"].sum())) else 0
        n_b, n_s = len(buys), len(sells)
        is_open  = (n_b > n_s) or n_s == 0
        fb = buys["transaction_date"].min()
        ls = sells["transaction_date"].max() if not sells.empty else None
        name = tk_t["asset"].mode()
        name = clean(name.iloc[0]) if not name.empty else tk

        rendite = None
        if YF_OK:
            hold_end = ls if not is_open and ls else p_end
            eff_s = max(fb, p_start)
            eff_e = min(hold_end, p_end)
            if eff_s < eff_e:
                try:
                    h = yf.Ticker(tk).history(
                        start=eff_s.strftime("%Y-%m-%d"),
                        end=(eff_e + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                        auto_adjust=True,
                    )
                    if not h.empty and len(h) >= 2:
                        rendite = round((float(h["Close"].iloc[-1]) / float(h["Close"].iloc[0]) - 1) * 100, 1)
                except Exception:
                    pass

        positions.append({
            "ticker":      tk,
            "name":        name,
            "is_open":     is_open,
            "n_buys":      n_b,
            "n_sells":     n_s,
            "buy_vol":     bv,
            "sell_vol":    sv,
            "first_buy":   str(fb.date()) if pd.notna(fb) else None,
            "last_sell":   str(ls.date()) if ls and pd.notna(ls) else None,
            "rendite_pct": rendite,
            "gewinn_ca":   round(bv * rendite / 100, 0) if rendite and bv else None,
        })

    positions.sort(key=lambda x: (x["rendite_pct"] or -999), reverse=True)
    return {"positions": positions}
