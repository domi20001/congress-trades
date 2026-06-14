"""
import_kaggle.py
===============
Einmaliger Import des Kaggle-Datensatzes
"US Senate Financial Disclosures (Stocks & Options)" in die lokale SQLite-DB.

Kaggle-Datensatz:
  https://www.kaggle.com/datasets/lukekerbs/us-senate-financial-disclosures-stocks-and-options

Verwendung:
  python import_kaggle.py                        # sucht CSV automatisch
  python import_kaggle.py pfad/zur/datei.csv     # expliziter Pfad
"""

import os
import sys
import glob
import hashlib
import sqlite3
import datetime as dt

import pandas as pd

# ── Pfad zur Datenbank (gleicher Ordner wie dieses Skript) ────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades_history.db")


# ── Datenbank vorbereiten ─────────────────────────────────────────────────
def init_db(con: sqlite3.Connection):
    con.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            trade_id        TEXT PRIMARY KEY,
            politician      TEXT,
            chamber         TEXT,
            district        TEXT,
            owner           TEXT,
            ticker          TEXT,
            asset           TEXT,
            asset_type      TEXT,
            direction       TEXT,
            transaction_type TEXT,
            amount_range    TEXT,
            amount_mid      REAL,
            transaction_date TEXT,
            disclosure_date TEXT,
            source_url      TEXT,
            first_seen      TEXT
        )
    """)
    con.commit()


# ── Hilfsfunktionen ───────────────────────────────────────────────────────
def make_trade_id(politician: str, ticker: str, transaction_date: str,
                  amount_range: str, direction: str, owner: str) -> str:
    parts = [str(x) for x in [politician, ticker, transaction_date,
                               amount_range, direction, owner]]
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def build_amount_range(low, high) -> str:
    """Baut aus asset_value_low / asset_value_high eine lesbare Spanne."""
    try:
        lo = int(float(low))
        hi = int(float(high))
        return f"${lo:,} - ${hi:,}"
    except (TypeError, ValueError):
        return ""


def amount_mid(low, high) -> float | None:
    try:
        return (float(low) + float(high)) / 2
    except (TypeError, ValueError):
        return None


def classify_direction(t: str) -> str:
    if not isinstance(t, str):
        return "Unbekannt"
    t = t.lower()
    if "purchase" in t or "buy" in t:
        return "Kauf"
    if "sale" in t or "sell" in t:
        return "Verkauf"
    return "Sonstige"


# ── CSV laden & normalisieren ─────────────────────────────────────────────
def load_csv(path: str) -> pd.DataFrame:
    print(f"  Lese CSV: {path}")
    df = pd.read_csv(path, low_memory=False)
    print(f"  Gefundene Spalten : {list(df.columns)}")
    print(f"  Zeilen in CSV     : {len(df):,}")

    # ── Spaltennamen vereinheitlichen (Kaggle-Datensatz hat inkonsistente Namen) ──
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Politiker-Name
    fn = df.get("first_name", pd.Series([""] * len(df))).fillna("")
    ln = df.get("last_name",  pd.Series([""] * len(df))).fillna("")
    df["politician"] = (fn + " " + ln).str.strip()
    # Fallback: manchmal gibt es nur "senator_name" oder "name"
    for fallback in ["senator_name", "name", "office"]:
        if fallback in df.columns:
            mask = df["politician"].str.strip() == ""
            df.loc[mask, "politician"] = df.loc[mask, fallback].fillna("")

    # Ticker bereinigen (Kaggle enthält manchmal "--" für unbekannte)
    df["ticker"] = df.get("ticker", pd.Series([None] * len(df)))
    df["ticker"] = df["ticker"].astype(str).str.strip()
    df.loc[df["ticker"].isin(["--", "nan", "N/A", ""]), "ticker"] = None

    # Unternehmensname
    df["asset"] = df.get("asset_name", df.get("asset_description",
                    pd.Series([None] * len(df)))).fillna("")

    # Transaktionstyp & Richtung
    tx_col = "transaction" if "transaction" in df.columns else "type"
    df["transaction_type"] = df.get(tx_col, pd.Series([""] * len(df))).fillna("")
    df["direction"] = df["transaction_type"].apply(classify_direction)

    # Betragsspanne
    lo_col = next((c for c in df.columns if "low"  in c and "value" in c), None)
    hi_col = next((c for c in df.columns if "high" in c and "value" in c), None)
    if lo_col and hi_col:
        df["amount_range"] = df.apply(
            lambda r: build_amount_range(r[lo_col], r[hi_col]), axis=1)
        df["amount_mid"] = df.apply(
            lambda r: amount_mid(r[lo_col], r[hi_col]), axis=1)
    else:
        # Fallback: "amount"-Spalte (z. B. senate-stock-watcher Format)
        amt_col = next((c for c in df.columns if "amount" in c), None)
        df["amount_range"] = df[amt_col].fillna("") if amt_col else ""
        df["amount_mid"] = None

    # Datum
    df["transaction_date"] = pd.to_datetime(
        df.get("transaction_date", pd.Series([None] * len(df))), errors="coerce")
    # Kaggle hat kein separates disclosure_date
    df["disclosure_date"] = pd.to_datetime(
        df.get("disclosure_date", df.get("date_received",
               df.get("date_recieved", pd.Series([None] * len(df))))),
        errors="coerce")

    # Kammer: Kaggle enthält nur Senatsdaten
    df["chamber"] = "Senat"
    df["district"] = df.get("state", df.get("district",
                     pd.Series([None] * len(df)))).fillna("")
    df["owner"] = df.get("owner", pd.Series(["Self"] * len(df))).fillna("Self")
    df["asset_type"] = df.get("asset_type", pd.Series(["Stock"] * len(df))).fillna("Stock")
    df["source_url"] = df.get("ptr_link", df.get("source_url",
                       pd.Series([None] * len(df)))).fillna("")

    return df


# ── In DB schreiben ───────────────────────────────────────────────────────
def import_to_db(df: pd.DataFrame, con: sqlite3.Connection) -> tuple[int, int]:
    now = dt.datetime.now().isoformat(timespec="seconds")
    added = 0
    skipped = 0

    for _, row in df.iterrows():
        pol  = str(row.get("politician", "") or "")
        tick = str(row.get("ticker", "") or "")
        tdate = str(row["transaction_date"]) if pd.notna(row.get("transaction_date")) else ""
        arange = str(row.get("amount_range", "") or "")
        direct = str(row.get("direction", "") or "")
        owner  = str(row.get("owner", "") or "")

        trade_id = make_trade_id(pol, tick, tdate, arange, direct, owner)

        try:
            cur = con.execute(
                """INSERT OR IGNORE INTO trades
                   (trade_id, politician, chamber, district, owner, ticker, asset,
                    asset_type, direction, transaction_type, amount_range, amount_mid,
                    transaction_date, disclosure_date, source_url, first_seen)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (trade_id, pol,
                 str(row.get("chamber", "Senat")),
                 str(row.get("district", "") or ""),
                 owner, tick if tick != "None" else None,
                 str(row.get("asset", "") or ""),
                 str(row.get("asset_type", "Stock") or "Stock"),
                 direct,
                 str(row.get("transaction_type", "") or ""),
                 arange,
                 float(row["amount_mid"]) if pd.notna(row.get("amount_mid")) else None,
                 tdate if tdate != "NaT" else None,
                 str(row["disclosure_date"]) if pd.notna(row.get("disclosure_date")) else None,
                 str(row.get("source_url", "") or ""),
                 now),
            )
            if cur.rowcount:
                added += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ⚠️  Fehler bei Zeile (übersprungen): {e}")
            skipped += 1

    con.commit()
    return added, skipped


# ── CSV-Datei finden ──────────────────────────────────────────────────────
def find_csv(explicit: str | None) -> str:
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        raise FileNotFoundError(f"Datei nicht gefunden: {explicit}")

    # Suche im gleichen Ordner nach passenden CSVs
    candidates = (
        glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.csv"))
    )
    if not candidates:
        raise FileNotFoundError(
            "Keine CSV-Datei im aktuellen Ordner gefunden.\n"
            "Verwendung: python import_kaggle.py pfad/zur/datei.csv"
        )
    if len(candidates) == 1:
        return candidates[0]

    # Mehrere CSVs: bevorzuge Dateien mit "senate" oder "disclosure" im Namen
    for c in candidates:
        name = os.path.basename(c).lower()
        if any(kw in name for kw in ["senate", "disclosure", "congress", "trade"]):
            return c

    # Fallback: erste Datei alphabetisch
    return sorted(candidates)[0]


# ── Hauptprogramm ─────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Kaggle → trades_history.db  Import")
    print("=" * 60)

    # CSV-Pfad ermitteln
    explicit = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        csv_path = find_csv(explicit)
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)

    # Daten laden
    try:
        df = load_csv(csv_path)
    except Exception as e:
        print(f"\n❌ Fehler beim Lesen der CSV: {e}")
        sys.exit(1)

    # Vorschau
    print(f"\n  Erste 3 Zeilen nach Normalisierung:")
    preview_cols = ["politician", "ticker", "asset", "direction",
                    "amount_range", "transaction_date"]
    print(df[[c for c in preview_cols if c in df.columns]].head(3).to_string(index=False))

    # Bestätigung
    print(f"\n  Datenbank: {DB_PATH}")
    print(f"  Zu importierende Zeilen: {len(df):,}")
    antwort = input("\n  Import starten? [j/N] ").strip().lower()
    if antwort not in ("j", "ja", "y", "yes"):
        print("  Abgebrochen.")
        sys.exit(0)

    # Import
    con = sqlite3.connect(DB_PATH)
    init_db(con)

    vorher = con.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    print(f"\n  Trades in DB vor Import : {vorher:,}")
    print("  Importiere …")

    added, skipped = import_to_db(df, con)

    nachher = con.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    print(f"\n  ✅ Fertig!")
    print(f"  Neu hinzugefügt : {added:,}")
    print(f"  Duplikate skip  : {skipped:,}")
    print(f"  Trades in DB    : {nachher:,}  (vorher: {vorher:,})")

    # Kurze Vorschau der importierten Daten
    sample = pd.read_sql_query(
        "SELECT politician, ticker, direction, transaction_date "
        "FROM trades ORDER BY transaction_date ASC LIMIT 5",
        con
    )
    print(f"\n  Älteste 5 Trades in DB:")
    print(sample.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
