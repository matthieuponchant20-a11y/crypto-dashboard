import numpy as np
import pandas as pd

# ========== RSI (Relative Strength Index) ==========
def rsi(series, period=14):
    """Calcule le RSI (accepte pd.Series, numpy array, ou liste)."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ========== MACD (Moving Average Convergence Divergence) ==========
def macd(series, fast=12, slow=26, signal=9):
    """Retourne (MACD, Signal, Histogram)."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# ========== Bollinger Bands ==========
def bollinger_bands(series, window=20, num_std=2):
    """Retourne (upper_band, middle_band, lower_band)."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    middle_band = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    return upper_band, middle_band, lower_band

# ========== SMA (Simple Moving Average) ==========
def sma(series, window=20):
    """Moyenne mobile simple."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    return series.rolling(window=window).mean()

# ========== EMA (Exponential Moving Average) ==========
def ema(series, window=20):
    """Moyenne mobile exponentielle."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    return series.ewm(span=window, adjust=False).mean()

# ========== Stochastic Oscillator ==========
def stochastic(series, k_period=14, d_period=3):
    """Retourne (%K, %D)."""
    if not isinstance(series, pd.Series):  # ✅ Convertit si nécessaire
        series = pd.Series(series)
    low_min = series.rolling(window=k_period).min()
    high_max = series.rolling(window=k_period).max()
    k = 100 * (series - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()
    return k, d