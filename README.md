# SupertrendPro Institutional V5.0.2 — Hedge Fund Style Cloud Fix

This package preserves the hedge-fund visual design and all analytics while removing the runtime dependency created by `pandas.Styler.background_gradient()`.

## Fix
- Replaced `background_gradient()` with a pure-CSS red/neutral/green institutional gradient.
- No matplotlib dependency is required.
- Existing tabs, charts, signals, risk metrics, TA-Lib auto engine and institutional price panel are preserved.

Deploy both `app.py` and `requirements.txt`, then reboot the Streamlit Cloud app.
