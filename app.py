# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# BIST PRO TECHNICAL ANALYZER – NO SYNTHETIC DATA
# Trend Following + Smart Supertrend + Beta + Risk Metrics
# Expanded BIST Blue-Chip Universe + Capital Gain Leaders Lab
# -------------------------------------------------------------------------
# Save as: bist_scanner_trend_beta_PRO_NO_SYNTHETIC.py
# Run:
#   streamlit run bist_scanner_trend_beta_PRO_NO_SYNTHETIC.py --server.port 8516
# -------------------------------------------------------------------------

import warnings
warnings.filterwarnings("ignore")

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import itertools

# -------------------------------------------------------------------------
# OPTIONAL TA-LIB: the app runs even if TA-Lib is not installed.
# No synthetic prices are ever generated; only indicator formulas fall back.
# -------------------------------------------------------------------------
try:
    import talib as ta
    TALIB_AVAILABLE = True
except Exception:
    ta = None
    TALIB_AVAILABLE = False

TRADING_DAYS = 252
ROLLING_BETA_WINDOW = 60
ROLLING_VOL_WINDOW = 63
MIN_PRICE_OBS = 120
BENCHMARK_SYMBOL = "XU100.IS"

st.set_page_config(
    layout="wide",
    page_title="BIST PRO Technical Scanner – No Synthetic Data",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------------
# STYLING
# -------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.0rem; padding-bottom: 2rem;}
      div[data-testid="stMetricValue"] {font-size: 1.35rem;}
      div[data-testid="stMetricLabel"] {font-size: .88rem; color: #475467;}
      .small-note {font-size: 0.86rem; color:#667085;}
      .risk-note {background:#fff7ed; border:1px solid #fed7aa; padding:12px 14px; border-radius:12px; color:#7c2d12;}
      .ok-note {background:#ecfdf3; border:1px solid #abefc6; padding:12px 14px; border-radius:12px; color:#054f31;}
      .mk-title {font-weight: 700; letter-spacing: -0.02em;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------------
# MARKET UNIVERSE – EXPANDED BIST BLUE CHIPS + USER'S CAPITAL GAIN LIST
# No synthetic data: tickers are used only to fetch real Yahoo Finance data.
# -------------------------------------------------------------------------
MARKET_DATA: Dict[str, Dict[str, str]] = {
    "Indices": {
        "BIST 100 Index": "XU100.IS",
        "BIST 30 Index": "XU030.IS",
        "BIST Bank Index": "XBANK.IS",
        "BIST Industrial Index": "XUSIN.IS",
        "BIST Holding & Investment Index": "XHOLD.IS",
    },
    "Major Banks & Financials": {
        "Akbank": "AKBNK.IS",
        "Garanti BBVA": "GARAN.IS",
        "Is Bankasi (C)": "ISCTR.IS",
        "Yapi Kredi": "YKBNK.IS",
        "QNB Bank": "QNBTR.IS",
        "VakifBank": "VAKBN.IS",
        "Halkbank": "HALKB.IS",
        "TSKB": "TSKB.IS",
        "Albaraka Turk": "ALBRK.IS",
        "Sekerbank": "SKBNK.IS",
        "Turkiye Sigorta": "TURSG.IS",
        "Anadolu Hayat Emeklilik": "ANHYT.IS",
        "Aksigorta": "AKGRT.IS",
        "Ray Sigorta": "RAYSG.IS",
        "Is Leasing": "ISFIN.IS",
        "Garanti Factoring": "GARFA.IS",
        "Vakif Leasing": "VAKFN.IS",
        "Lider Factoring": "LIDFA.IS",
    },
    "Holdings & Conglomerates": {
        "Koc Holding": "KCHOL.IS",
        "Sabanci Holding": "SAHOL.IS",
        "Anadolu Grubu Holding": "AGHOL.IS",
        "Dogus Otomotiv": "DOAS.IS",
        "GSD Holding": "GSDHO.IS",
        "Bera Holding": "BERA.IS",
        "Eczacibasi Yatirim": "ECZYT.IS",
        "Is Yatirim Menkul": "ISMEN.IS",
    },
    "Transport, Aviation & Tourism": {
        "Turkish Airlines": "THYAO.IS",
        "Pegasus Airlines": "PGSUS.IS",
        "TAV Airports": "TAVHL.IS",
        "Tureks Turizm": "TUREX.IS",
        "Merit Turizm": "MERIT.IS",
    },
    "Industrial Blue Chips": {
        "Tupras": "TUPRS.IS",
        "Aselsan": "ASELS.IS",
        "Eregli Steel": "EREGL.IS",
        "Kardemir D": "KRDMD.IS",
        "Kardemir A": "KRDMA.IS",
        "Ford Otosan": "FROTO.IS",
        "Tofas Auto": "TOASO.IS",
        "Arcelik": "ARCLK.IS",
        "Sisecam": "SISE.IS",
        "Enka Construction": "ENKAI.IS",
        "Brisa": "BRISA.IS",
        "Karsan": "KARSN.IS",
        "Erbosan": "ERBOS.IS",
    },
    "Consumer, Retail & Food": {
        "BIM Markets": "BIMAS.IS",
        "Migros": "MGROS.IS",
        "Coca-Cola Icecek": "CCOLA.IS",
        "Ulker Biskuvi": "ULKER.IS",
        "Mavi Giyim": "MAVI.IS",
        "Desa Deri": "DESA.IS",
        "Kervan Gida": "KRVGD.IS",
        "Konfrut Gida": "KNFRT.IS",
        "Besler Gida": "BESLR.IS",
        "Aygaz": "AYGAZ.IS",
        "Sok Marketler": "SOKM.IS",
        "Anadolu Efes": "AEFES.IS",
    },
    "Technology & Telecom": {
        "Turkcell": "TCELL.IS",
        "Turk Telekom": "TTKOM.IS",
        "Logo Yazilim": "LOGO.IS",
        "Link Bilgisayar": "LINK.IS",
        "Penta Teknoloji": "PENTA.IS",
        "Escort Teknoloji": "ESCOM.IS",
        "Kron Teknoloji": "KRONT.IS",
        "Indeks Bilgisayar": "INDES.IS",
    },
    "Energy, Materials & Construction": {
        "Astor Energy": "ASTOR.IS",
        "Sasa Polyester": "SASA.IS",
        "Hektas": "HEKTS.IS",
        "Petkim": "PETKM.IS",
        "Koza Altin": "KOZAL.IS",
        "Smart Gunes": "SMRTG.IS",
        "Eupower Enerji": "EUPWR.IS",
        "Gesan": "GESAN.IS",
        "Kalekim": "KLKIM.IS",
        "QUA Granite": "QUAGR.IS",
        "Kütahya Porselen": "KUTPO.IS",
    },
    "Real Estate & Other": {
        "Torunlar GYO": "TRGYO.IS",
        "Servet GYO": "SRVGY.IS",
        "Emlak Konut GYO": "EKGYO.IS",
        "Ozak GYO": "OZKGY.IS",
        "MLP Saglik": "MPARK.IS",
    },
}

# User-provided top capital-gain list as a fixed screener basket.
# These snapshot fields are metadata only. Time-series calculations use real Yahoo data.
CAPITAL_GAIN_LEADERS = [
    {"Name": "Tureks Turizm Tasimacilik", "Symbol": "TUREX.IS", "SnapshotPrice": 6.86, "SnapshotGainPct": 65.73, "SnapshotTarget": 11.37, "Rating": "Very Good"},
    {"Name": "Link Bilgisayar", "Symbol": "LINK.IS", "SnapshotPrice": 6.94, "SnapshotGainPct": 60.90, "SnapshotTarget": 11.15, "Rating": "Excellent"},
    {"Name": "Kalekim", "Symbol": "KLKIM.IS", "SnapshotPrice": 27.12, "SnapshotGainPct": 58.26, "SnapshotTarget": 42.89, "Rating": "Very Good"},
    {"Name": "Kutahya Porselen", "Symbol": "KUTPO.IS", "SnapshotPrice": 84.50, "SnapshotGainPct": 57.91, "SnapshotTarget": 133.434, "Rating": "Good"},
    {"Name": "Aygaz", "Symbol": "AYGAZ.IS", "SnapshotPrice": 232.80, "SnapshotGainPct": 56.96, "SnapshotTarget": 365.09, "Rating": "Good"},
    {"Name": "Besler Gida", "Symbol": "BESLR.IS", "SnapshotPrice": 13.18, "SnapshotGainPct": 54.38, "SnapshotTarget": 20.35, "Rating": "Good"},
    {"Name": "QUA Granite", "Symbol": "QUAGR.IS", "SnapshotPrice": 3.49, "SnapshotGainPct": 53.31, "SnapshotTarget": 5.35, "Rating": "Fair"},
    {"Name": "Servet GYO", "Symbol": "SRVGY.IS", "SnapshotPrice": 2.64, "SnapshotGainPct": 51.76, "SnapshotTarget": 3.991, "Rating": "Good"},
    {"Name": "Mavi Giyim", "Symbol": "MAVI.IS", "SnapshotPrice": 37.88, "SnapshotGainPct": 51.57, "SnapshotTarget": 57.35, "Rating": "Very Good"},
    {"Name": "Desa Deri", "Symbol": "DESA.IS", "SnapshotPrice": 10.43, "SnapshotGainPct": 48.08, "SnapshotTarget": 15.46, "Rating": "Very Good"},
    {"Name": "Ford Otosan", "Symbol": "FROTO.IS", "SnapshotPrice": 81.05, "SnapshotGainPct": 47.65, "SnapshotTarget": 119.74, "Rating": "Very Good"},
    {"Name": "Penta Teknoloji", "Symbol": "PENTA.IS", "SnapshotPrice": 13.27, "SnapshotGainPct": 47.57, "SnapshotTarget": 19.58, "Rating": "Very Good"},
    {"Name": "Ray Sigorta", "Symbol": "RAYSG.IS", "SnapshotPrice": 177.90, "SnapshotGainPct": 47.06, "SnapshotTarget": 261.62, "Rating": "Excellent"},
    {"Name": "Is Bankasi C", "Symbol": "ISCTR.IS", "SnapshotPrice": 14.19, "SnapshotGainPct": 46.25, "SnapshotTarget": 20.753, "Rating": "Good"},
    {"Name": "Kardemir D", "Symbol": "KRDMD.IS", "SnapshotPrice": 36.82, "SnapshotGainPct": 46.21, "SnapshotTarget": 53.864, "Rating": "Good"},
    {"Name": "Logo Yazilim", "Symbol": "LOGO.IS", "SnapshotPrice": 138.20, "SnapshotGainPct": 45.47, "SnapshotTarget": 201.04, "Rating": "Very Good"},
    {"Name": "Escort Teknoloji", "Symbol": "ESCOM.IS", "SnapshotPrice": 6.14, "SnapshotGainPct": 45.40, "SnapshotTarget": 8.91, "Rating": "Very Good"},
    {"Name": "Karsan", "Symbol": "KARSN.IS", "SnapshotPrice": 11.96, "SnapshotGainPct": 44.34, "SnapshotTarget": 17.277, "Rating": "Excellent"},
    {"Name": "Konfrut Gida", "Symbol": "KNFRT.IS", "SnapshotPrice": 11.88, "SnapshotGainPct": 42.97, "SnapshotTarget": 16.98, "Rating": "Fair"},
    {"Name": "Erbosan", "Symbol": "ERBOS.IS", "SnapshotPrice": 169.50, "SnapshotGainPct": 40.96, "SnapshotTarget": 238.93, "Rating": "Good"},
    {"Name": "Kardemir A", "Symbol": "KRDMA.IS", "SnapshotPrice": 38.18, "SnapshotGainPct": 40.91, "SnapshotTarget": 53.799, "Rating": "Good"},
    {"Name": "Merit Turizm", "Symbol": "MERIT.IS", "SnapshotPrice": 17.99, "SnapshotGainPct": 39.62, "SnapshotTarget": 25.006, "Rating": "Excellent"},
    {"Name": "GSD Holding", "Symbol": "GSDHO.IS", "SnapshotPrice": 5.57, "SnapshotGainPct": 39.21, "SnapshotTarget": 7.768, "Rating": "Very Good"},
    {"Name": "Lider Faktoring", "Symbol": "LIDFA.IS", "SnapshotPrice": 2.78, "SnapshotGainPct": 38.70, "SnapshotTarget": 3.856, "Rating": "Good"},
    {"Name": "Bera Holding", "Symbol": "BERA.IS", "SnapshotPrice": 14.97, "SnapshotGainPct": 38.26, "SnapshotTarget": 20.684, "Rating": "Fair"},
    {"Name": "Brisa", "Symbol": "BRISA.IS", "SnapshotPrice": 80.95, "SnapshotGainPct": 38.20, "SnapshotTarget": 111.87, "Rating": "Good"},
    {"Name": "Kervan Gida", "Symbol": "KRVGD.IS", "SnapshotPrice": 2.76, "SnapshotGainPct": 37.78, "SnapshotTarget": 3.80, "Rating": "Good"},
    {"Name": "TAV Airports", "Symbol": "TAVHL.IS", "SnapshotPrice": 263.75, "SnapshotGainPct": 36.94, "SnapshotTarget": 360.84, "Rating": "Good"},
    {"Name": "Tofas Auto", "Symbol": "TOASO.IS", "SnapshotPrice": 298.75, "SnapshotGainPct": 36.51, "SnapshotTarget": 407.82, "Rating": "Good"},
    {"Name": "Ulker Biskuvi", "Symbol": "ULKER.IS", "SnapshotPrice": np.nan, "SnapshotGainPct": np.nan, "SnapshotTarget": np.nan, "Rating": "User List"},
]

UNIVERSE_STOCKS: Dict[str, str] = {}
for _category, _mapping in MARKET_DATA.items():
    if _category == "Indices":
        continue
    UNIVERSE_STOCKS.update(_mapping)

CAPITAL_GAIN_SYMBOL_TO_NAME = {row["Symbol"]: row["Name"] for row in CAPITAL_GAIN_LEADERS}
ALL_ANALYSIS_SYMBOLS = sorted(set(UNIVERSE_STOCKS.values()).union(CAPITAL_GAIN_SYMBOL_TO_NAME.keys()))
SYMBOL_TO_NAME = {v: k for k, m in MARKET_DATA.items() if k != "Indices" for v in []}
for cat, mapping in MARKET_DATA.items():
    if cat != "Indices":
        for name, sym in mapping.items():
            SYMBOL_TO_NAME[sym] = name
for row in CAPITAL_GAIN_LEADERS:
    SYMBOL_TO_NAME.setdefault(row["Symbol"], row["Name"])

# -------------------------------------------------------------------------
# INDICATOR FALLBACKS
# -------------------------------------------------------------------------
def _series(x, index=None):
    return pd.Series(x, index=index).astype(float)


def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False, min_periods=span).mean()


def rsi(s: pd.Series, period: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - sma) / (0.015 * mad.replace(0, np.nan))


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    # Wilder-style ADX approximation; TA-Lib used when available.
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)
    tr = atr(high, low, close, period)
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / tr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / tr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def macd_calc(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    m = ema(close, fast) - ema(close, slow)
    sig = ema(m, signal)
    return m, sig, m - sig


def bbands(close: pd.Series, period: int = 20, ndev: float = 2.0):
    mid = close.rolling(period).mean()
    sd = close.rolling(period).std()
    return mid + ndev * sd, mid, mid - ndev * sd

# -------------------------------------------------------------------------
# DATA FETCHING: REAL YAHOO DATA ONLY
# -------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def get_data(symbol: str, start, end) -> Optional[pd.DataFrame]:
    """Download OHLCV data from Yahoo Finance. Returns None if unavailable.

    Data governance: no proxy, no interpolation, no synthetic fallback.
    """
    try:
        download_start = pd.to_datetime(start) - pd.DateOffset(years=2)
        df = yf.download(
            symbol,
            start=download_start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is None or df.empty:
            return None
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(c in df.columns for c in required_cols):
            return None
        df = df[required_cols].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None) if getattr(df.index, "tz", None) is not None else pd.to_datetime(df.index)
        df = df.loc[~df.index.duplicated(keep="last")].sort_index()
        df = df.dropna(how="any")
        df = df[(df["Close"] > 0) & (df["High"] >= df["Low"])]
        return df if len(df) > 0 else None
    except Exception:
        return None


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    high, low, close, volume = df["High"], df["Low"], df["Close"], df["Volume"]
    c = close.values.astype(float)
    h = high.values.astype(float)
    l = low.values.astype(float)
    v = volume.values.astype(float)

    if TALIB_AVAILABLE:
        df["RSI"] = ta.RSI(c, timeperiod=14)
        df["EMA_20"] = ta.EMA(c, timeperiod=20)
        df["EMA_50"] = ta.EMA(c, timeperiod=50)
        df["EMA_100"] = ta.EMA(c, timeperiod=100)
        df["EMA_200"] = ta.EMA(c, timeperiod=200)
        df["CCI"] = ta.CCI(h, l, c, timeperiod=20)
        df["ATR"] = ta.ATR(h, l, c, timeperiod=14)
        df["ADX"] = ta.ADX(h, l, c, timeperiod=14)
        macd, macd_signal, macd_hist = ta.MACD(c, fastperiod=12, slowperiod=26, signalperiod=9)
        upper, middle, lower = ta.BBANDS(c, timeperiod=20, nbdevup=2, nbdevdn=2)
        df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = macd, macd_signal, macd_hist
        df["BB_UPPER"], df["BB_MID"], df["BB_LOWER"] = upper, middle, lower
    else:
        df["RSI"] = rsi(close, 14)
        df["EMA_20"] = ema(close, 20)
        df["EMA_50"] = ema(close, 50)
        df["EMA_100"] = ema(close, 100)
        df["EMA_200"] = ema(close, 200)
        df["CCI"] = cci(high, low, close, 20)
        df["ATR"] = atr(high, low, close, 14)
        df["ADX"] = adx(high, low, close, 14)
        m, sig, hist = macd_calc(close)
        df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = m, sig, hist
        up, mid, lo = bbands(close, 20, 2)
        df["BB_UPPER"], df["BB_MID"], df["BB_LOWER"] = up, mid, lo

    df["Return"] = df["Close"].pct_change()
    df["Log_Return"] = np.log(df["Close"] / df["Close"].shift(1))
    df["Dollar_Volume"] = df["Close"] * df["Volume"]
    df["Vol_20D_Ann"] = df["Return"].rolling(20).std() * np.sqrt(TRADING_DAYS)
    df["Vol_63D_Ann"] = df["Return"].rolling(63).std() * np.sqrt(TRADING_DAYS)
    df["Momentum_20D"] = df["Close"].pct_change(20)
    df["Momentum_63D"] = df["Close"].pct_change(63)
    df["Momentum_126D"] = df["Close"].pct_change(126)
    df["Momentum_252D"] = df["Close"].pct_change(252)
    df["High_252D"] = df["Close"].rolling(252).max()
    df["Low_252D"] = df["Close"].rolling(252).min()
    df["Pct_From_52W_High"] = df["Close"] / df["High_252D"] - 1
    df["Pct_From_52W_Low"] = df["Close"] / df["Low_252D"] - 1
    df["Drawdown"] = df["Close"] / df["Close"].cummax() - 1
    df["ATR_Pct"] = df["ATR"] / df["Close"]
    df = df.dropna(subset=["Close", "RSI", "EMA_50", "EMA_200", "ATR", "ADX", "MACD", "MACD_SIGNAL"])
    return df


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    high, low, close = df["High"], df["Low"], df["Close"]
    atr_series = atr(high, low, close, period)
    if TALIB_AVAILABLE:
        atr_series = pd.Series(ta.ATR(high.values, low.values, close.values, timeperiod=period), index=df.index)
    hl2 = (high + low) / 2.0
    basic_ub = hl2 + multiplier * atr_series
    basic_lb = hl2 - multiplier * atr_series
    final_ub = basic_ub.copy()
    final_lb = basic_lb.copy()
    trend = pd.Series(0, index=df.index, dtype=float)
    st_line = pd.Series(np.nan, index=df.index, dtype=float)

    for i in range(1, len(df)):
        if np.isnan(basic_ub.iloc[i]) or np.isnan(basic_lb.iloc[i]):
            continue
        final_ub.iloc[i] = basic_ub.iloc[i] if (basic_ub.iloc[i] < final_ub.iloc[i - 1] or close.iloc[i - 1] > final_ub.iloc[i - 1]) else final_ub.iloc[i - 1]
        final_lb.iloc[i] = basic_lb.iloc[i] if (basic_lb.iloc[i] > final_lb.iloc[i - 1] or close.iloc[i - 1] < final_lb.iloc[i - 1]) else final_lb.iloc[i - 1]
        prev_trend = trend.iloc[i - 1] if trend.iloc[i - 1] != 0 else 1
        if prev_trend == 1 and close.iloc[i] < final_lb.iloc[i]:
            trend.iloc[i] = -1
        elif prev_trend == -1 and close.iloc[i] > final_ub.iloc[i]:
            trend.iloc[i] = 1
        else:
            trend.iloc[i] = prev_trend
        st_line.iloc[i] = final_lb.iloc[i] if trend.iloc[i] == 1 else final_ub.iloc[i]
    return st_line, trend

# -------------------------------------------------------------------------
# RISK METRICS
# -------------------------------------------------------------------------
def max_drawdown(equity: pd.Series) -> float:
    eq = pd.Series(equity).dropna()
    if eq.empty:
        return np.nan
    return float((eq / eq.cummax() - 1).min())


def safe_cagr(ret: pd.Series) -> float:
    r = pd.Series(ret).dropna()
    if r.empty:
        return np.nan
    total = (1 + r).prod() - 1
    years = len(r) / TRADING_DAYS
    if years <= 0 or 1 + total <= 0:
        return np.nan
    return float((1 + total) ** (1 / years) - 1)


def tail_risk(r: pd.Series, alpha: float = 0.95):
    x = pd.Series(r).dropna()
    if len(x) < 20:
        return np.nan, np.nan
    var = -np.quantile(x, 1 - alpha)
    cvar = -x[x <= np.quantile(x, 1 - alpha)].mean()
    return float(var), float(cvar)


def compute_return_metrics(ret: pd.Series, benchmark_ret: Optional[pd.Series] = None, name: str = "Series") -> Dict[str, float]:
    r = pd.Series(ret).dropna().astype(float)
    if r.empty:
        return {"Name": name}
    eq = (1 + r).cumprod()
    cagr = safe_cagr(r)
    vol = float(r.std() * np.sqrt(TRADING_DAYS)) if r.std() > 0 else np.nan
    downside = r[r < 0].std() * np.sqrt(TRADING_DAYS) if (r < 0).sum() > 2 else np.nan
    sharpe = cagr / vol if vol and vol > 0 else np.nan
    sortino = cagr / downside if downside and downside > 0 else np.nan
    mdd = max_drawdown(eq)
    calmar = cagr / abs(mdd) if mdd and mdd < 0 else np.nan
    var95, cvar95 = tail_risk(r, 0.95)
    var99, cvar99 = tail_risk(r, 0.99)

    beta = alpha = tracking_error = info_ratio = corr = np.nan
    if benchmark_ret is not None:
        b = pd.Series(benchmark_ret).reindex(r.index).dropna()
        common = r.index.intersection(b.index)
        rr, bb = r.reindex(common).dropna(), b.reindex(common).dropna()
        common = rr.index.intersection(bb.index)
        rr, bb = rr.reindex(common), bb.reindex(common)
        if len(rr) > 20 and bb.var() > 0:
            beta = float(np.cov(rr, bb, ddof=1)[0, 1] / np.var(bb, ddof=1))
            alpha = float((rr.mean() - beta * bb.mean()) * TRADING_DAYS)
            active = rr - bb
            tracking_error = float(active.std() * np.sqrt(TRADING_DAYS))
            info_ratio = float(active.mean() * TRADING_DAYS / tracking_error) if tracking_error > 0 else np.nan
            corr = float(rr.corr(bb))

    return {
        "Name": name,
        "Total Return %": ((1 + r).prod() - 1) * 100,
        "CAGR %": cagr * 100 if pd.notna(cagr) else np.nan,
        "Ann Vol %": vol * 100 if pd.notna(vol) else np.nan,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "Calmar": calmar,
        "Max Drawdown %": mdd * 100 if pd.notna(mdd) else np.nan,
        "VaR 95% %": var95 * 100 if pd.notna(var95) else np.nan,
        "CVaR 95% %": cvar95 * 100 if pd.notna(cvar95) else np.nan,
        "VaR 99% %": var99 * 100 if pd.notna(var99) else np.nan,
        "CVaR 99% %": cvar99 * 100 if pd.notna(cvar99) else np.nan,
        "Beta vs XU100": beta,
        "Alpha Ann %": alpha * 100 if pd.notna(alpha) else np.nan,
        "Tracking Error %": tracking_error * 100 if pd.notna(tracking_error) else np.nan,
        "Information Ratio": info_ratio,
        "Correlation vs XU100": corr,
    }


def compute_stats(df: pd.DataFrame, trades: list, index_returns: Optional[pd.Series] = None):
    df = df.copy()
    df["BH_Equity"] = (1 + df["Return"].fillna(0)).cumprod()
    df["Strategy_Equity"] = (1 + df["Strategy_Return"].fillna(0)).cumprod()
    bh = compute_return_metrics(df["Return"], index_returns, name="Buy & Hold")
    stg = compute_return_metrics(df["Strategy_Return"], index_returns, name="Strategy")

    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        wins = trades_df[trades_df["Return"] > 0]
        losses = trades_df[trades_df["Return"] <= 0]
        gross_profit = wins["Return"].sum()
        gross_loss = losses["Return"].sum()
        trade_stats = {
            "trade_count": len(trades_df),
            "win_rate": len(wins) / len(trades_df) * 100,
            "avg_trade": trades_df["Return"].mean() * 100,
            "avg_win": wins["Return"].mean() * 100 if not wins.empty else np.nan,
            "avg_loss": losses["Return"].mean() * 100 if not losses.empty else np.nan,
            "profit_factor": gross_profit / abs(gross_loss) if gross_loss < 0 else np.nan,
            "avg_hold": trades_df["HoldingDays"].mean(),
        }
    else:
        trade_stats = {"trade_count": 0, "win_rate": 0.0, "avg_trade": 0.0, "avg_win": np.nan, "avg_loss": np.nan, "profit_factor": np.nan, "avg_hold": np.nan}

    pos_mask = df["Return"] > 0
    neg_mask = df["Return"] < 0
    up_capture = (df.loc[pos_mask, "Strategy_Return"].sum() / df.loc[pos_mask, "Return"].sum() * 100) if pos_mask.any() and df.loc[pos_mask, "Return"].sum() != 0 else np.nan
    down_capture = (df.loc[neg_mask, "Strategy_Return"].sum() / df.loc[neg_mask, "Return"].sum() * 100) if neg_mask.any() and df.loc[neg_mask, "Return"].sum() != 0 else np.nan
    directional = ((np.sign(df["Return"]) == np.sign(df["Strategy_Return"])).mean() * 100) if len(df) else np.nan

    stats = {
        "bh_total_pct": bh.get("Total Return %", np.nan),
        "strat_total_pct": stg.get("Total Return %", np.nan),
        "bh_annual_pct": bh.get("CAGR %", np.nan),
        "strat_annual_pct": stg.get("CAGR %", np.nan),
        "bh_mdd_pct": bh.get("Max Drawdown %", np.nan),
        "strat_mdd_pct": stg.get("Max Drawdown %", np.nan),
        "sharpe": stg.get("Sharpe", np.nan),
        "sortino": stg.get("Sortino", np.nan),
        "calmar": stg.get("Calmar", np.nan),
        "var95_pct": stg.get("VaR 95% %", np.nan),
        "cvar95_pct": stg.get("CVaR 95% %", np.nan),
        "var99_pct": stg.get("VaR 99% %", np.nan),
        "cvar99_pct": stg.get("CVaR 99% %", np.nan),
        "beta_asset": bh.get("Beta vs XU100", np.nan),
        "beta_strategy": stg.get("Beta vs XU100", np.nan),
        "alpha_strategy_pct": stg.get("Alpha Ann %", np.nan),
        "tracking_error_pct": stg.get("Tracking Error %", np.nan),
        "information_ratio": stg.get("Information Ratio", np.nan),
        "up_capture_pct": up_capture,
        "down_capture_pct": down_capture,
        "directional_match_pct": directional,
        "corr_bh": df["BH_Equity"].corr(df["Strategy_Equity"]),
    }
    stats.update(trade_stats)
    return trades_df, stats


def add_rolling_beta(df: pd.DataFrame, index_returns: Optional[pd.Series]) -> pd.DataFrame:
    df = df.copy()
    if index_returns is None or len(index_returns) == 0:
        df["Rolling_Beta_Asset"] = np.nan
        df["Rolling_Beta_Strategy"] = np.nan
        return df
    pair = pd.DataFrame({
        "asset": df["Return"],
        "strategy": df["Strategy_Return"],
        "index": index_returns.reindex(df.index),
    }).dropna()
    if len(pair) >= ROLLING_BETA_WINDOW:
        roll_var = pair["index"].rolling(ROLLING_BETA_WINDOW).var()
        df["Rolling_Beta_Asset"] = (pair["asset"].rolling(ROLLING_BETA_WINDOW).cov(pair["index"]) / roll_var).reindex(df.index).ffill()
        df["Rolling_Beta_Strategy"] = (pair["strategy"].rolling(ROLLING_BETA_WINDOW).cov(pair["index"]) / roll_var).reindex(df.index).ffill()
    else:
        df["Rolling_Beta_Asset"] = np.nan
        df["Rolling_Beta_Strategy"] = np.nan
    return df

# -------------------------------------------------------------------------
# BACKTESTS
# -------------------------------------------------------------------------
def backtest_macd_atr_trailing(
    df: pd.DataFrame,
    start_date,
    atr_mult_stop: float = 2.0,
    use_rsi_exit: bool = False,
    rsi_exit_level: float = 30.0,
    use_ema_filter: bool = False,
    use_adx_filter: bool = False,
    adx_threshold: float = 10.0,
    use_macd_exit: bool = False,
    fastperiod: int = 8,
    slowperiod: int = 21,
    signalperiod: int = 9,
    market_filter=None,
    index_returns: Optional[pd.Series] = None,
):
    df = df.copy()
    df = df[df.index >= pd.Timestamp(start_date)].copy()
    if df.empty:
        return df, pd.DataFrame(), {}

    m, sig, hist = macd_calc(df["Close"], fastperiod, slowperiod, signalperiod)
    if TALIB_AVAILABLE:
        m0, s0, h0 = ta.MACD(df["Close"].values, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        m, sig, hist = pd.Series(m0, index=df.index), pd.Series(s0, index=df.index), pd.Series(h0, index=df.index)
    df["MACD"], df["MACD_SIGNAL"], df["MACD_HIST"] = m, sig, hist

    bull_cross = (df["MACD"] > df["MACD_SIGNAL"]) & (df["MACD"].shift(1) <= df["MACD_SIGNAL"].shift(1))
    bear_cross = (df["MACD"] < df["MACD_SIGNAL"]) & (df["MACD"].shift(1) >= df["MACD_SIGNAL"].shift(1))
    entry_long = bull_cross.fillna(False)
    if use_ema_filter:
        entry_long &= df["Close"] > df["EMA_200"]
    if use_adx_filter:
        entry_long &= df["ADX"] > adx_threshold
    if market_filter is not None:
        entry_long &= market_filter.reindex(df.index).ffill().fillna(False)

    exit_rule = pd.Series(False, index=df.index)
    if use_macd_exit:
        exit_rule |= bear_cross.fillna(False)
    if use_rsi_exit:
        exit_rule |= (df["RSI"] < rsi_exit_level).fillna(False)

    return _run_trailing_backtest(df, entry_long, exit_rule, atr_mult_stop, "MACD/RSI_EXIT", index_returns)


def backtest_supertrend_trailing(
    df: pd.DataFrame,
    start_date,
    st_period: int = 10,
    st_mult: float = 2.5,
    use_adx_filter: bool = False,
    adx_threshold: float = 10.0,
    use_ema_filter: bool = False,
    atr_mult_stop: float = 2.0,
    market_filter=None,
    index_returns: Optional[pd.Series] = None,
):
    df = df.copy()
    st_line, st_dir = compute_supertrend(df, st_period, st_mult)
    df["ST_Line"] = st_line
    df["ST_Dir"] = st_dir
    df = df[df.index >= pd.Timestamp(start_date)].copy()
    if df.empty:
        return df, pd.DataFrame(), {}
    df["ST_Dir_prev"] = df["ST_Dir"].shift(1).fillna(0)
    entry_long = (df["ST_Dir"] == 1) & (df["ST_Dir_prev"] != 1)
    if use_ema_filter:
        entry_long &= df["Close"] > df["EMA_200"]
    if use_adx_filter:
        entry_long &= df["ADX"] > adx_threshold
    if market_filter is not None:
        entry_long &= market_filter.reindex(df.index).ffill().fillna(False)
    exit_rule = ((df["ST_Dir"] == -1) & (df["ST_Dir_prev"] == 1)).fillna(False)
    return _run_trailing_backtest(df, entry_long.fillna(False), exit_rule, atr_mult_stop, "SUPERTREND_FLIP", index_returns)


def _run_trailing_backtest(df: pd.DataFrame, entry_long: pd.Series, exit_rule: pd.Series, atr_mult_stop: float, exit_label: str, index_returns: Optional[pd.Series]):
    position = 0
    signals, positions, atr_stops = [], [], []
    entry_price = None
    entry_index = None
    peak_price = None
    stop_level = np.nan
    trades = []

    for i, (idx, row) in enumerate(df.iterrows()):
        price = float(row["Close"])
        atr_value = float(row["ATR"])
        buy = bool(entry_long.iloc[i])
        exit_today = bool(exit_rule.iloc[i])
        hit_stop = False

        if position == 1:
            peak_price = max(peak_price if peak_price is not None else price, price)
            new_stop = peak_price - atr_mult_stop * atr_value
            stop_level = new_stop if np.isnan(stop_level) else max(stop_level, new_stop)
            hit_stop = price <= stop_level

        if position == 0:
            if buy:
                position = 1
                entry_price = price
                entry_index = idx
                peak_price = price
                stop_level = price - atr_mult_stop * atr_value
                signal = 1
            else:
                signal = 0
        else:
            reason = "ATR_TRAILING_STOP" if hit_stop else (exit_label if exit_today else None)
            if reason is not None:
                position = 0
                signal = -1
                ret = price / entry_price - 1.0 if entry_price else np.nan
                trades.append({
                    "EntryDate": entry_index,
                    "ExitDate": idx,
                    "EntryPrice": entry_price,
                    "ExitPrice": price,
                    "Return": ret,
                    "ReturnPct": ret * 100,
                    "HoldingDays": (idx - entry_index).days if entry_index is not None else np.nan,
                    "ExitReason": reason,
                })
                entry_price = None
                entry_index = None
                peak_price = None
                stop_level = np.nan
            else:
                signal = 0

        signals.append(signal)
        positions.append(position)
        atr_stops.append(stop_level if position == 1 else np.nan)

    df["Signal"] = signals
    df["Position"] = positions
    df["ATR_Stop"] = atr_stops
    df["Return"] = df["Close"].pct_change().fillna(0.0)
    df["Strategy_Return"] = df["Position"].shift(1).fillna(0) * df["Return"]
    df["BH_Equity"] = (1 + df["Return"]).cumprod()
    df["Strategy_Equity"] = (1 + df["Strategy_Return"]).cumprod()
    df["Strategy_Drawdown"] = df["Strategy_Equity"] / df["Strategy_Equity"].cummax() - 1
    df = add_rolling_beta(df, index_returns)
    trades_df, stats = compute_stats(df, trades, index_returns=index_returns)
    return df, trades_df, stats

# -------------------------------------------------------------------------
# SCREENER HELPERS
# -------------------------------------------------------------------------
def technical_grade(last: pd.Series) -> Tuple[float, str]:
    score = 0.0
    reasons = []
    if last["Close"] > last["EMA_200"]:
        score += 20; reasons.append("Price>EMA200")
    if last["EMA_50"] > last["EMA_200"]:
        score += 15; reasons.append("EMA50>EMA200")
    if last["MACD"] > last["MACD_SIGNAL"]:
        score += 12; reasons.append("MACD+")
    if 45 <= last["RSI"] <= 70:
        score += 15; reasons.append("Healthy RSI")
    elif last["RSI"] > 70:
        score += 5; reasons.append("Overbought RSI")
    if last["ADX"] >= 20:
        score += 12; reasons.append("Trend ADX")
    if pd.notna(last.get("Momentum_63D", np.nan)) and last["Momentum_63D"] > 0:
        score += 10; reasons.append("3M Momentum+")
    if pd.notna(last.get("Momentum_126D", np.nan)) and last["Momentum_126D"] > 0:
        score += 8; reasons.append("6M Momentum+")
    if pd.notna(last.get("Pct_From_52W_High", np.nan)) and last["Pct_From_52W_High"] > -0.15:
        score += 8; reasons.append("Near 52W high")
    return min(score, 100.0), ", ".join(reasons)


def analyze_symbol(symbol: str, name: str, start_date, end_date, index_returns: Optional[pd.Series], min_obs: int = MIN_PRICE_OBS):
    raw = get_data(symbol, start_date, end_date)
    if raw is None or len(raw) < min_obs:
        return None, {"Name": name, "Symbol": symbol, "Status": "Excluded", "Reason": f"Insufficient Yahoo data (<{min_obs} rows)"}
    ind = compute_indicators(raw)
    if len(ind) < min_obs:
        return None, {"Name": name, "Symbol": symbol, "Status": "Excluded", "Reason": "Insufficient indicator-ready rows"}
    last = ind.iloc[-1]
    returns = ind["Return"].dropna()
    bench = index_returns.reindex(returns.index).dropna() if index_returns is not None else None
    metrics = compute_return_metrics(returns, bench, name=name)
    tech_score, reasons = technical_grade(last)

    row = {
        "Name": name,
        "Symbol": symbol,
        "Last Close": last["Close"],
        "RSI": last["RSI"],
        "ADX": last["ADX"],
        "ATR %": last["ATR_Pct"] * 100,
        "20D Momentum %": last.get("Momentum_20D", np.nan) * 100,
        "3M Momentum %": last.get("Momentum_63D", np.nan) * 100,
        "6M Momentum %": last.get("Momentum_126D", np.nan) * 100,
        "1Y Momentum %": last.get("Momentum_252D", np.nan) * 100,
        "From 52W High %": last.get("Pct_From_52W_High", np.nan) * 100,
        "From 52W Low %": last.get("Pct_From_52W_Low", np.nan) * 100,
        "Ann Vol %": metrics.get("Ann Vol %", np.nan),
        "CAGR %": metrics.get("CAGR %", np.nan),
        "Max Drawdown %": metrics.get("Max Drawdown %", np.nan),
        "Sharpe": metrics.get("Sharpe", np.nan),
        "Sortino": metrics.get("Sortino", np.nan),
        "Calmar": metrics.get("Calmar", np.nan),
        "Beta vs XU100": metrics.get("Beta vs XU100", np.nan),
        "VaR 95% %": metrics.get("VaR 95% %", np.nan),
        "CVaR 95% %": metrics.get("CVaR 95% %", np.nan),
        "Avg Daily TL Volume": ind["Dollar_Volume"].tail(60).mean(),
        "Technical Score": tech_score,
        "Signal Drivers": reasons,
        "Status": "OK",
        "Reason": "",
    }
    return ind, row


def run_universe_scan(name_to_symbol: Dict[str, str], start_date, end_date, index_returns: Optional[pd.Series], min_obs: int = MIN_PRICE_OBS):
    rows, excluded, data_map = [], [], {}
    progress = st.progress(0.0)
    items = list(name_to_symbol.items())
    for i, (name, symbol) in enumerate(items):
        ind, row = analyze_symbol(symbol, name, start_date, end_date, index_returns, min_obs=min_obs)
        if ind is not None:
            data_map[symbol] = ind
            rows.append(row)
        else:
            excluded.append(row)
        progress.progress((i + 1) / max(len(items), 1))
    progress.empty()
    return pd.DataFrame(rows), pd.DataFrame(excluded), data_map


def smart_score_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    x = df.copy()
    # Composite score: trend quality + risk-adjusted return + liquidity + drawdown control.
    for col in ["Technical Score", "Sharpe", "Sortino", "3M Momentum %", "6M Momentum %", "Avg Daily TL Volume", "Max Drawdown %"]:
        if col not in x.columns:
            x[col] = np.nan
    def rank_pct(s, higher=True):
        return s.rank(pct=True, ascending=not higher) * 100
    x["Composite Score"] = (
        0.30 * x["Technical Score"] +
        0.20 * rank_pct(x["Sharpe"].fillna(-999), True) +
        0.15 * rank_pct(x["3M Momentum %"].fillna(-999), True) +
        0.15 * rank_pct(x["6M Momentum %"].fillna(-999), True) +
        0.10 * rank_pct(x["Avg Daily TL Volume"].fillna(0), True) +
        0.10 * rank_pct(x["Max Drawdown %"].fillna(-999), True)
    )
    x["Action Lens"] = np.select(
        [x["Composite Score"] >= 75, x["Composite Score"] >= 55, x["Composite Score"] >= 35],
        ["Leadership Watch", "Constructive", "Neutral / Validate",],
        default="High Risk / Weak"
    )
    return x.sort_values("Composite Score", ascending=False)

# -------------------------------------------------------------------------
# PORTFOLIO LAB
# -------------------------------------------------------------------------
def run_equal_weight_portfolio(symbols: List[str], start_date, end_date, idx_ind: Optional[pd.DataFrame] = None, min_len: int = 120):
    if not symbols:
        return None
    prices = {}
    for sym in symbols:
        raw = get_data(sym, start_date, end_date)
        if raw is None or len(raw) < min_len:
            continue
        ind = compute_indicators(raw)
        if len(ind) >= min_len:
            prices[sym] = ind["Close"]
    if len(prices) < 2:
        return None
    px_df = pd.concat(prices, axis=1, join="inner").dropna()
    if px_df.shape[0] < 60:
        return None
    ret = px_df.pct_change().dropna()
    port_ret = ret.mean(axis=1)
    idx_ret = None
    if idx_ind is not None and "Close" in idx_ind.columns:
        idx_ret = idx_ind["Close"].reindex(ret.index).ffill().pct_change().dropna()
        common = port_ret.index.intersection(idx_ret.index)
        port_ret, idx_ret, ret = port_ret.reindex(common), idx_ret.reindex(common), ret.reindex(common)
    return {
        "prices": px_df,
        "returns": ret,
        "port_ret": port_ret,
        "idx_ret": idx_ret,
        "eq_port": (1 + port_ret).cumprod(),
        "eq_index": (1 + idx_ret).cumprod() if idx_ret is not None else None,
        "corr": ret.corr(),
        "asset_total_ret": (1 + ret).prod() - 1,
        "metrics_port": compute_return_metrics(port_ret, idx_ret, "Equal Weight Basket"),
        "metrics_index": compute_return_metrics(idx_ret, None, "XU100") if idx_ret is not None else {},
    }

# -------------------------------------------------------------------------
# PLOT HELPERS
# -------------------------------------------------------------------------
def clean_fig(fig, height=520):
    fig.update_layout(
        template="plotly_white",
        height=height,
        hovermode="x unified",
        margin=dict(l=18, r=18, t=55, b=22),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#eef2f6", rangeslider_visible=False)
    fig.update_yaxes(showgrid=True, gridcolor="#eef2f6")
    return fig


def strategy_chart(p: pd.DataFrame, title: str):
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.025,
        row_heights=[0.42, 0.16, 0.14, 0.14, 0.14],
        subplot_titles=(title, "MACD", "RSI", "ATR %", "Strategy Drawdown"),
    )
    fig.add_trace(go.Scatter(x=p.index, y=p["Close"], mode="lines", name="Adjusted Close", line=dict(width=1.7)), row=1, col=1)
    for col, name, dash in [("EMA_50", "EMA 50", "dot"), ("EMA_200", "EMA 200", "solid"), ("BB_UPPER", "BB Upper", "dash"), ("BB_LOWER", "BB Lower", "dash")]:
        if col in p.columns:
            fig.add_trace(go.Scatter(x=p.index, y=p[col], mode="lines", name=name, line=dict(width=1.0, dash=dash)), row=1, col=1)
    if "ATR_Stop" in p.columns:
        fig.add_trace(go.Scatter(x=p.index, y=p["ATR_Stop"], mode="lines", name="ATR Stop", line=dict(width=1.2, dash="dot")), row=1, col=1)
    buys = p[p.get("Signal", 0) == 1]
    sells = p[p.get("Signal", 0) == -1]
    if not buys.empty:
        fig.add_trace(go.Scatter(x=buys.index, y=buys["Close"], mode="markers", name="BUY", marker=dict(symbol="triangle-up", size=11, line=dict(width=1, color="black"))), row=1, col=1)
    if not sells.empty:
        fig.add_trace(go.Scatter(x=sells.index, y=sells["Close"], mode="markers", name="SELL", marker=dict(symbol="triangle-down", size=11, line=dict(width=1, color="black"))), row=1, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["MACD"], mode="lines", name="MACD", line=dict(width=1.3)), row=2, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["MACD_SIGNAL"], mode="lines", name="MACD Signal", line=dict(width=1.1, dash="dot")), row=2, col=1)
    fig.add_trace(go.Bar(x=p.index, y=p["MACD_HIST"], name="MACD Hist"), row=2, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["RSI"], mode="lines", name="RSI", line=dict(width=1.4)), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, opacity=0.08, line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, opacity=0.08, line_width=0, row=3, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["ATR_Pct"] * 100, mode="lines", name="ATR %", line=dict(width=1.3)), row=4, col=1)
    dd_col = "Strategy_Drawdown" if "Strategy_Drawdown" in p.columns else "Drawdown"
    fig.add_trace(go.Scatter(x=p.index, y=p[dd_col] * 100, mode="lines", name="Drawdown %", fill="tozeroy"), row=5, col=1)
    fig.update_yaxes(title_text="TRY", row=1, col=1)
    fig.update_yaxes(title_text="%", row=4, col=1)
    fig.update_yaxes(title_text="%", row=5, col=1)
    return clean_fig(fig, height=1040)


def equity_risk_chart(p: pd.DataFrame):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.42, 0.28, 0.30], subplot_titles=("Equity Curves", "Rolling 60D Beta vs XU100", "Return Distribution"))
    fig.add_trace(go.Scatter(x=p.index, y=p["BH_Equity"], name="Buy & Hold", mode="lines", line=dict(width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["Strategy_Equity"], name="Strategy", mode="lines", line=dict(width=2.0)), row=1, col=1)
    if "Rolling_Beta_Asset" in p.columns:
        fig.add_trace(go.Scatter(x=p.index, y=p["Rolling_Beta_Asset"], name="Asset Beta", mode="lines"), row=2, col=1)
        fig.add_trace(go.Scatter(x=p.index, y=p["Rolling_Beta_Strategy"], name="Strategy Beta", mode="lines"), row=2, col=1)
    fig.add_trace(go.Histogram(x=p["Strategy_Return"] * 100, nbinsx=80, name="Strategy Daily Return %"), row=3, col=1)
    return clean_fig(fig, height=880)


def risk_return_bubble(df: pd.DataFrame, title: str):
    if df.empty:
        return go.Figure()
    plot_df = df.copy()
    plot_df["Bubble"] = np.sqrt(plot_df["Avg Daily TL Volume"].clip(lower=0).fillna(0))
    fig = px.scatter(
        plot_df,
        x="Ann Vol %",
        y="CAGR %",
        size="Bubble",
        hover_name="Name",
        hover_data=["Symbol", "Sharpe", "Max Drawdown %", "Beta vs XU100", "Technical Score", "Composite Score"],
        text="Symbol",
        title=title,
    )
    fig.update_traces(textposition="top center", marker=dict(opacity=0.72, line=dict(width=0.7, color="#475467")))
    return clean_fig(fig, height=650)


def momentum_bar(df: pd.DataFrame, title: str, n: int = 20):
    if df.empty:
        return go.Figure()
    cols = ["Name", "Symbol", "3M Momentum %", "6M Momentum %", "1Y Momentum %", "Composite Score"]
    tmp = df[[c for c in cols if c in df.columns]].head(n).sort_values("Composite Score")
    fig = go.Figure()
    fig.add_trace(go.Bar(y=tmp["Symbol"], x=tmp["3M Momentum %"], orientation="h", name="3M"))
    fig.add_trace(go.Bar(y=tmp["Symbol"], x=tmp["6M Momentum %"], orientation="h", name="6M"))
    fig.update_layout(barmode="group", title=title, xaxis_title="Momentum %", yaxis_title="Ticker")
    return clean_fig(fig, height=620)


def corr_heatmap(corr: pd.DataFrame, title: str):
    fig = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1, colorbar=dict(title="Corr")))
    fig.update_layout(title=title)
    return clean_fig(fig, height=650)


def style_smart_table(df: pd.DataFrame):
    fmt_cols = {c: "{:.2f}" for c in df.select_dtypes(include=[np.number]).columns}
    pct_cols = [c for c in df.columns if "%" in c or c in ["ATR %", "From 52W High %", "From 52W Low %"]]
    for c in pct_cols:
        if c in fmt_cols:
            fmt_cols[c] = "{:.2f}%"
    sty = df.style.format(fmt_cols, na_rep="N/A")
    for c in ["Composite Score", "Technical Score", "Sharpe", "Sortino", "CAGR %", "3M Momentum %", "6M Momentum %"]:
        if c in df.columns:
            sty = sty.background_gradient(subset=[c])
    return sty

# -------------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------------
st.sidebar.title("📊 BIST PRO Scanner")
st.sidebar.caption("Real Yahoo Finance daily data only. No synthetic price series, no proxy fallback.")

selected_category = st.sidebar.selectbox("Select Sector / Category:", list(MARKET_DATA.keys()), index=2)
ticker_options = MARKET_DATA[selected_category]
selected_asset_name = st.sidebar.selectbox("Select Asset:", list(ticker_options.keys()))
ticker_symbol = ticker_options[selected_asset_name]

st.sidebar.markdown("---")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2018-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today") + pd.Timedelta(days=1))

st.sidebar.markdown("---")
use_index_filter_global = st.sidebar.checkbox("Use BIST 100 Regime Filter (XU100 > EMA200)", value=True)
strategy_choice = st.sidebar.radio("Select Strategy Variant:", ["MACD + ATR Trailing", "Smart Supertrend", "Smart Supertrend + Optimizer"], index=1)

if strategy_choice.startswith("MACD"):
    st.sidebar.subheader("MACD + ATR Parameters")
    atr_mult_stop_macd = st.sidebar.slider("ATR Trailing Stop Multiplier", 0.5, 6.0, 2.0, 0.5)
    use_rsi_exit = st.sidebar.checkbox("Use RSI Exit Filter", False)
    rsi_exit_level = st.sidebar.slider("RSI Exit Threshold", 20, 50, 30)
    use_macd_exit = st.sidebar.checkbox("Use MACD Exit (Bear Cross)", False)
    use_ema_macd = st.sidebar.checkbox("Use EMA200 Filter (Entry)", False)
    use_adx_macd = st.sidebar.checkbox("Use ADX Filter (Entry)", False)
    adx_threshold_macd = st.sidebar.slider("ADX Threshold (MACD)", 5, 40, 10)
    macd_fast = st.sidebar.slider("MACD Fast Period", 5, 20, 8, 1)
    macd_slow = st.sidebar.slider("MACD Slow Period", 10, 40, 21, 1)
    macd_signal = st.sidebar.slider("MACD Signal Period", 5, 20, 9, 1)
else:
    st.sidebar.subheader("Smart Supertrend Parameters")
    st_period = st.sidebar.slider("Supertrend Period", 7, 50, 10)
    st_mult = st.sidebar.slider("Supertrend Multiplier", 1.0, 6.0, 2.5, 0.5)
    use_adx_filter = st.sidebar.checkbox("Use ADX Filter", True)
    adx_threshold = st.sidebar.slider("ADX Threshold", 5, 40, 10)
    use_ema_filter = st.sidebar.checkbox("Use EMA200 Filter (Entry)", True)
    atr_mult_stop_st = st.sidebar.slider("ATR Trailing Stop Multiplier", 0.5, 6.0, 2.0, 0.5)

# -------------------------------------------------------------------------
# MAIN DATA LOAD
# -------------------------------------------------------------------------
st.markdown("<h1 class='mk-title'>BIST PRO Technical Scanner — Trend, Beta, Risk & Capital Gain Leaders</h1>", unsafe_allow_html=True)
st.caption("MK FinTECH LabGEN @2026 Istanbul | No synthetic data | Yahoo Finance daily OHLCV | Educational analytics, not investment advice")

if not TALIB_AVAILABLE:
    st.info("TA-Lib is not installed. The app is using internal pandas/numpy indicator formulas. Price data still comes only from Yahoo Finance.")

with st.spinner("Fetching XU100 benchmark for regime filter and beta calculations..."):
    idx_raw = get_data(BENCHMARK_SYMBOL, start_date, end_date)
idx_ind, index_returns, index_regime = None, None, None
if idx_raw is not None and len(idx_raw) > 260:
    idx_ind = compute_indicators(idx_raw)
    index_returns = idx_ind["Close"].pct_change().fillna(0.0)
    index_regime = idx_ind["Close"] > idx_ind["EMA_200"]
else:
    st.warning("XU100 benchmark data is unavailable or insufficient. Beta, alpha and regime filter may be disabled.")
    use_index_filter_global = False

with st.spinner(f"Fetching real Yahoo data for {selected_asset_name} ({ticker_symbol})..."):
    data_raw = get_data(ticker_symbol, start_date, end_date)
if data_raw is None or len(data_raw) < 260:
    st.error(f"Insufficient Yahoo Finance data for {selected_asset_name} ({ticker_symbol}). No synthetic fallback is used.")
    st.stop()

data = compute_indicators(data_raw)
if strategy_choice.startswith("MACD"):
    plot_data, trades_df, stats = backtest_macd_atr_trailing(
        data, start_date=start_date,
        atr_mult_stop=atr_mult_stop_macd,
        use_rsi_exit=use_rsi_exit,
        rsi_exit_level=rsi_exit_level,
        use_ema_filter=use_ema_macd,
        use_adx_filter=use_adx_macd,
        adx_threshold=adx_threshold_macd,
        use_macd_exit=use_macd_exit,
        fastperiod=macd_fast,
        slowperiod=macd_slow,
        signalperiod=macd_signal,
        market_filter=index_regime if use_index_filter_global else None,
        index_returns=index_returns,
    )
else:
    plot_data, trades_df, stats = backtest_supertrend_trailing(
        data, start_date=start_date,
        st_period=st_period,
        st_mult=st_mult,
        use_adx_filter=use_adx_filter,
        adx_threshold=adx_threshold,
        use_ema_filter=use_ema_filter,
        atr_mult_stop=atr_mult_stop_st,
        market_filter=index_regime if use_index_filter_global else None,
        index_returns=index_returns,
    )

last = plot_data.iloc[-1]
trend_state = "BULLISH" if last["Close"] > last["EMA_200"] else "BEARISH"
tech_score, tech_reasons = technical_grade(last)

# Top KPIs
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Last Price", f"₺{last['Close']:.2f}")
k2.metric("RSI", f"{last['RSI']:.1f}")
k3.metric("Trend vs EMA200", trend_state)
k4.metric("Strategy Return", f"{stats.get('strat_total_pct', np.nan):.1f}%")
k5.metric("Strategy MaxDD", f"{stats.get('strat_mdd_pct', np.nan):.1f}%")
k6.metric("Technical Score", f"{tech_score:.0f}/100")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Strategy Chart",
    "📋 Smart Data Table",
    "📈 Technical Signals",
    "📊 Backtest & Risk",
    "🏦 Blue-Chip Universe Screener",
    "🚀 Capital Gain Leaders Lab",
    "🧮 Mini Portfolio Lab",
])

# -------------------------------------------------------------------------
# TAB 1
# -------------------------------------------------------------------------
with tab1:
    st.plotly_chart(strategy_chart(plot_data, f"{selected_asset_name} ({ticker_symbol}) — {strategy_choice}"), use_container_width=True, theme=None)
    st.markdown(f"<div class='ok-note'><b>Signal Drivers:</b> {tech_reasons or 'No strong technical driver detected.'}</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------------
# TAB 2
# -------------------------------------------------------------------------
with tab2:
    st.subheader("Smart Data Table — OHLCV, Signals, Risk & Rolling Beta")
    cols = ["Open", "High", "Low", "Close", "Volume", "RSI", "EMA_50", "EMA_200", "MACD", "MACD_SIGNAL", "ATR_Pct", "ADX", "Signal", "Position", "ATR_Stop", "Return", "Strategy_Return", "Rolling_Beta_Asset", "Rolling_Beta_Strategy", "Drawdown"]
    show = plot_data[[c for c in cols if c in plot_data.columns]].sort_index(ascending=False).copy()
    st.dataframe(style_smart_table(show.head(800)), use_container_width=True, height=620)
    csv = show.to_csv(index=True).encode("utf-8")
    st.download_button("Download current asset table as CSV", csv, file_name=f"{ticker_symbol.replace('.','_')}_smart_table.csv", mime="text/csv")
    if not trades_df.empty:
        st.subheader("Trade Log")
        st.dataframe(style_smart_table(trades_df.sort_values("EntryDate", ascending=False)), use_container_width=True)

# -------------------------------------------------------------------------
# TAB 3
# -------------------------------------------------------------------------
with tab3:
    st.subheader("Technical Signals — Candlestick, Bollinger Bands, Supertrend, RSI/MACD")
    ts = plot_data.copy()
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.58, 0.22, 0.20], subplot_titles=("Candlestick + Bollinger + EMA + Supertrend", "MACD", "RSI"))
    fig.add_trace(go.Candlestick(x=ts.index, open=ts["Open"], high=ts["High"], low=ts["Low"], close=ts["Close"], name="OHLC"), row=1, col=1)
    for c, n, dash in [("BB_UPPER", "BB Upper", "dash"), ("BB_MID", "BB Mid", "dot"), ("BB_LOWER", "BB Lower", "dash"), ("EMA_50", "EMA50", "dot"), ("EMA_200", "EMA200", "solid"), ("ST_Line", "Supertrend", "solid")]:
        if c in ts.columns:
            fig.add_trace(go.Scatter(x=ts.index, y=ts[c], name=n, mode="lines", line=dict(width=1.1, dash=dash)), row=1, col=1)
    fig.add_trace(go.Scatter(x=ts.index, y=ts["MACD"], name="MACD", mode="lines"), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts.index, y=ts["MACD_SIGNAL"], name="Signal", mode="lines", line=dict(dash="dot")), row=2, col=1)
    fig.add_trace(go.Bar(x=ts.index, y=ts["MACD_HIST"], name="Hist"), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts.index, y=ts["RSI"], name="RSI", mode="lines"), row=3, col=1)
    fig.add_hrect(y0=70, y1=100, opacity=0.08, line_width=0, row=3, col=1)
    fig.add_hrect(y0=0, y1=30, opacity=0.08, line_width=0, row=3, col=1)
    st.plotly_chart(clean_fig(fig, height=900), use_container_width=True, theme=None)

# -------------------------------------------------------------------------
# TAB 4
# -------------------------------------------------------------------------
with tab4:
    st.subheader("Backtest, Beta & Institutional Risk Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Strategy CAGR", f"{stats.get('strat_annual_pct', np.nan):.2f}%")
    c2.metric("Sharpe / Sortino", f"{stats.get('sharpe', np.nan):.2f} / {stats.get('sortino', np.nan):.2f}")
    c3.metric("Beta vs XU100", f"{stats.get('beta_strategy', np.nan):.2f}")
    c4.metric("IR / TE", f"{stats.get('information_ratio', np.nan):.2f} / {stats.get('tracking_error_pct', np.nan):.1f}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("VaR 95% / CVaR 95%", f"{stats.get('var95_pct', np.nan):.2f}% / {stats.get('cvar95_pct', np.nan):.2f}%")
    c6.metric("VaR 99% / CVaR 99%", f"{stats.get('var99_pct', np.nan):.2f}% / {stats.get('cvar99_pct', np.nan):.2f}%")
    c7.metric("Up / Down Capture", f"{stats.get('up_capture_pct', np.nan):.1f}% / {stats.get('down_capture_pct', np.nan):.1f}%")
    c8.metric("Win Rate / Trades", f"{stats.get('win_rate', np.nan):.1f}% / {stats.get('trade_count', 0)}")

    st.plotly_chart(equity_risk_chart(plot_data), use_container_width=True, theme=None)

    risk_table = pd.DataFrame([compute_return_metrics(plot_data["Return"], index_returns, "Buy & Hold"), compute_return_metrics(plot_data["Strategy_Return"], index_returns, "Strategy")])
    st.dataframe(style_smart_table(risk_table), use_container_width=True)

    if strategy_choice == "Smart Supertrend + Optimizer":
        st.markdown("---")
        st.subheader("Smart Supertrend Recent-Window Optimization")
        opt_window = st.slider("Optimization Window Days", 90, 540, 180, 30)
        if st.button("Run Optimization Grid"):
            rows = []
            combos = list(itertools.product([7, 10, 14, 20, 30], [1.5, 2.0, 2.5, 3.0, 4.0], [5, 10, 15, 20]))
            prog = st.progress(0.0)
            opt_start = plot_data.index[-1] - pd.Timedelta(days=opt_window)
            for i, (per, mult, adx_th) in enumerate(combos):
                bt, tr, stt = backtest_supertrend_trailing(data, opt_start, per, mult, True, adx_th, use_ema_filter, atr_mult_stop_st, index_regime if use_index_filter_global else None, index_returns)
                rows.append({"Period": per, "Multiplier": mult, "ADX": adx_th, "Return %": stt.get("strat_total_pct", np.nan), "Sharpe": stt.get("sharpe", np.nan), "MaxDD %": stt.get("strat_mdd_pct", np.nan), "Trades": stt.get("trade_count", 0)})
                prog.progress((i + 1) / len(combos))
            prog.empty()
            opt_df = pd.DataFrame(rows).sort_values(["Sharpe", "Return %"], ascending=False)
            st.dataframe(style_smart_table(opt_df.head(30)), use_container_width=True)
            pivot = opt_df[opt_df["ADX"] == opt_df.iloc[0]["ADX"]].pivot_table(index="Period", columns="Multiplier", values="Return %", aggfunc="mean")
            st.plotly_chart(clean_fig(go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorbar=dict(title="Return %"))).update_layout(title="Return Heatmap for Best ADX Bucket"), height=500), use_container_width=True)

# -------------------------------------------------------------------------
# TAB 5: BLUE-CHIP UNIVERSE SCREENER
# -------------------------------------------------------------------------
with tab5:
    st.subheader("Expanded BIST Blue-Chip Universe Screener")
    st.markdown("<div class='small-note'>Universe includes banks, QNB, Garanti, YKBNK, Koç Holding, Sabancı Holding, Pegasus, industrials, telecom, consumer and energy names. Calculations use real Yahoo daily data only.</div>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    min_obs_scan = col_a.slider("Minimum valid observations", 60, 756, 180, 30, key="blue_min_obs")
    selected_groups = col_b.multiselect("Universe Groups", [k for k in MARKET_DATA.keys() if k != "Indices"], default=["Major Banks & Financials", "Holdings & Conglomerates", "Transport, Aviation & Tourism", "Industrial Blue Chips"])
    scan_limit = col_c.slider("Max names to show", 10, 100, 40, 5)

    selected_map = {}
    for group in selected_groups:
        selected_map.update(MARKET_DATA[group])

    if st.button("Run Blue-Chip Universe Scan"):
        with st.spinner("Scanning selected BIST universe with real Yahoo data..."):
            scan_df, excluded_df, data_map = run_universe_scan(selected_map, start_date, end_date, index_returns, min_obs=min_obs_scan)
            scan_df = smart_score_table(scan_df)
            st.session_state["blue_scan_df"] = scan_df
            st.session_state["blue_excluded_df"] = excluded_df
            st.session_state["blue_data_symbols"] = list(data_map.keys())

    scan_df = st.session_state.get("blue_scan_df", pd.DataFrame())
    if scan_df is not None and not scan_df.empty:
        st.success(f"Scan complete: {len(scan_df)} valid names. Excluded names are listed below, if any.")
        show_cols = ["Name", "Symbol", "Action Lens", "Composite Score", "Technical Score", "Last Close", "RSI", "ADX", "3M Momentum %", "6M Momentum %", "CAGR %", "Ann Vol %", "Sharpe", "Max Drawdown %", "Beta vs XU100", "Avg Daily TL Volume", "Signal Drivers"]
        st.dataframe(style_smart_table(scan_df[[c for c in show_cols if c in scan_df.columns]].head(scan_limit)), use_container_width=True, height=620)
        st.plotly_chart(risk_return_bubble(scan_df, "Blue-Chip Risk / Return / Liquidity Map"), use_container_width=True, theme=None)
        st.plotly_chart(momentum_bar(scan_df, "Top Blue-Chip Momentum Profile", n=min(20, len(scan_df))), use_container_width=True, theme=None)
        st.download_button("Download blue-chip screener CSV", scan_df.to_csv(index=False).encode("utf-8"), "bist_blue_chip_screener.csv", "text/csv")
    excluded_df = st.session_state.get("blue_excluded_df", pd.DataFrame())
    if excluded_df is not None and not excluded_df.empty:
        with st.expander("Data Quality / Exclusion Log"):
            st.dataframe(excluded_df, use_container_width=True)

# -------------------------------------------------------------------------
# TAB 6: CAPITAL GAIN LEADERS LAB
# -------------------------------------------------------------------------
with tab6:
    st.subheader("Capital Gain Leaders Lab — Separate High-Momentum Basket")
    st.markdown("<div class='risk-note'><b>No synthetic data rule:</b> the snapshot gain table is only a user-provided watchlist/metadata layer. All prices, returns, beta, volatility and signals below are recalculated from real Yahoo Finance OHLCV. If Yahoo data is missing, the stock is excluded and logged.</div>", unsafe_allow_html=True)
    cap_meta = pd.DataFrame(CAPITAL_GAIN_LEADERS)
    st.markdown("#### User-Provided Snapshot Watchlist")
    st.dataframe(style_smart_table(cap_meta), use_container_width=True, height=320)

    col1, col2, col3 = st.columns(3)
    min_obs_cap = col1.slider("Minimum valid observations", 40, 756, 120, 20, key="cap_min_obs")
    cap_top_n = col2.slider("Top N rows", 5, 40, 30, 5, key="cap_topn")
    rank_basis = col3.selectbox("Sort by", ["Composite Score", "3M Momentum %", "6M Momentum %", "Sharpe", "Technical Score", "SnapshotGainPct"], index=0)

    if st.button("Run Capital Gain Leaders Scan"):
        cap_map = {row["Name"]: row["Symbol"] for row in CAPITAL_GAIN_LEADERS}
        with st.spinner("Scanning capital gain leaders using real Yahoo data..."):
            cap_df, cap_excl, cap_data_map = run_universe_scan(cap_map, start_date, end_date, index_returns, min_obs=min_obs_cap)
            cap_df = smart_score_table(cap_df)
            if not cap_df.empty:
                cap_df = cap_df.merge(cap_meta[["Symbol", "SnapshotPrice", "SnapshotGainPct", "SnapshotTarget", "Rating"]], on="Symbol", how="left")
                if rank_basis in cap_df.columns:
                    cap_df = cap_df.sort_values(rank_basis, ascending=False)
            st.session_state["cap_df"] = cap_df
            st.session_state["cap_excl"] = cap_excl
            st.session_state["cap_data_symbols"] = list(cap_data_map.keys())

    cap_df = st.session_state.get("cap_df", pd.DataFrame())
    if cap_df is not None and not cap_df.empty:
        show_cols = ["Name", "Symbol", "Action Lens", "Composite Score", "SnapshotGainPct", "SnapshotTarget", "Rating", "Last Close", "RSI", "ADX", "3M Momentum %", "6M Momentum %", "1Y Momentum %", "From 52W High %", "ATR %", "Ann Vol %", "Sharpe", "Max Drawdown %", "Beta vs XU100", "VaR 95% %", "Avg Daily TL Volume", "Signal Drivers"]
        st.markdown("#### Capital Gain Leaders — Smart Ranking")
        st.dataframe(style_smart_table(cap_df[[c for c in show_cols if c in cap_df.columns]].head(cap_top_n)), use_container_width=True, height=650)
        c1, c2, c3 = st.columns(3)
        top = cap_df.iloc[0]
        c1.metric("Top Composite", f"{top['Name']} ({top['Symbol']})", f"{top['Composite Score']:.1f}")
        c2.metric("Best 3M Momentum", f"{cap_df.sort_values('3M Momentum %', ascending=False).iloc[0]['Symbol']}", f"{cap_df['3M Momentum %'].max():.1f}%")
        c3.metric("Highest Risk Vol", f"{cap_df.sort_values('Ann Vol %', ascending=False).iloc[0]['Symbol']}", f"{cap_df['Ann Vol %'].max():.1f}%")
        st.plotly_chart(risk_return_bubble(cap_df, "Capital Gain Leaders — Risk / Return / Liquidity Map"), use_container_width=True, theme=None)
        st.plotly_chart(momentum_bar(cap_df, "Capital Gain Leaders — Momentum Comparison", n=min(25, len(cap_df))), use_container_width=True, theme=None)
        st.download_button("Download capital gain leaders CSV", cap_df.to_csv(index=False).encode("utf-8"), "bist_capital_gain_leaders_scan.csv", "text/csv")
    cap_excl = st.session_state.get("cap_excl", pd.DataFrame())
    if cap_excl is not None and not cap_excl.empty:
        with st.expander("Capital Gain Leaders — Exclusion Log"):
            st.dataframe(cap_excl, use_container_width=True)

# -------------------------------------------------------------------------
# TAB 7: MINI PORTFOLIO LAB
# -------------------------------------------------------------------------
with tab7:
    st.subheader("Mini Equal-Weight Portfolio Lab vs XU100")
    source_choice = st.radio("Choose selection source", ["Manual Universe", "Top Blue-Chip Scan", "Top Capital Gain Leaders"], horizontal=True)
    if source_choice == "Manual Universe":
        all_names = list(UNIVERSE_STOCKS.keys())
        default_names = ["Akbank", "Garanti BBVA", "Yapi Kredi", "Koc Holding", "Sabanci Holding", "Pegasus Airlines", "Turkish Airlines", "Ford Otosan"]
        chosen_names = st.multiselect("Select stocks", all_names, default=[x for x in default_names if x in all_names])
        chosen_symbols = [UNIVERSE_STOCKS[n] for n in chosen_names]
    elif source_choice == "Top Blue-Chip Scan":
        scan_df = st.session_state.get("blue_scan_df", pd.DataFrame())
        if scan_df.empty:
            st.warning("Run the Blue-Chip Universe Scan first, or switch to Manual Universe.")
            chosen_symbols = []
        else:
            topn = st.slider("Top N from blue-chip scan", 3, min(20, len(scan_df)), min(8, len(scan_df)))
            chosen_symbols = scan_df.head(topn)["Symbol"].tolist()
            st.write(chosen_symbols)
    else:
        cap_df = st.session_state.get("cap_df", pd.DataFrame())
        if cap_df.empty:
            st.warning("Run the Capital Gain Leaders Scan first, or switch to Manual Universe.")
            chosen_symbols = []
        else:
            topn = st.slider("Top N from capital gain leaders", 3, min(20, len(cap_df)), min(8, len(cap_df)), key="cap_port_topn")
            chosen_symbols = cap_df.head(topn)["Symbol"].tolist()
            st.write(chosen_symbols)

    if st.button("Run Equal-Weight Portfolio Backtest"):
        with st.spinner("Building equal-weight portfolio from real Yahoo data..."):
            portfolio = run_equal_weight_portfolio(chosen_symbols, start_date, end_date, idx_ind=idx_ind, min_len=MIN_PRICE_OBS)
            st.session_state["portfolio_result"] = portfolio

    portfolio = st.session_state.get("portfolio_result", None)
    if portfolio is not None:
        if portfolio is None:
            st.error("Portfolio could not be created. Too few valid Yahoo Finance histories.")
        else:
            pmet = portfolio["metrics_port"]
            imet = portfolio.get("metrics_index", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Portfolio CAGR", f"{pmet.get('CAGR %', np.nan):.2f}%")
            c2.metric("Portfolio Vol", f"{pmet.get('Ann Vol %', np.nan):.2f}%")
            c3.metric("Sharpe", f"{pmet.get('Sharpe', np.nan):.2f}")
            c4.metric("MaxDD", f"{pmet.get('Max Drawdown %', np.nan):.2f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=portfolio["eq_port"].index, y=portfolio["eq_port"], mode="lines", name="Equal-Weight Basket"))
            if portfolio["eq_index"] is not None:
                fig.add_trace(go.Scatter(x=portfolio["eq_index"].index, y=portfolio["eq_index"], mode="lines", name="XU100"))
            fig.update_layout(title="Mini Portfolio Equity Curve vs XU100", yaxis_title="Normalized Equity")
            st.plotly_chart(clean_fig(fig, height=560), use_container_width=True, theme=None)

            st.markdown("#### Portfolio vs Benchmark Metrics")
            st.dataframe(style_smart_table(pd.DataFrame([pmet, imet])), use_container_width=True)
            st.markdown("#### Component Total Returns")
            comp = portfolio["asset_total_ret"].mul(100).sort_values(ascending=False).reset_index()
            comp.columns = ["Symbol", "Total Return %"]
            st.dataframe(style_smart_table(comp), use_container_width=True)
            st.plotly_chart(corr_heatmap(portfolio["corr"], "Portfolio Component Correlation Matrix"), use_container_width=True, theme=None)

