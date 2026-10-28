# ⚡ OptiVolt Industrial | B2B Power Capacity & Energy Audit SaaS

[![Streamlit App](https://static.streamlit.io/badge/streamlit_badge_black_white.svg)](https://optivolt.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)

Professional B2B engineering SaaS designed to mathematically optimize industrial electricity billing (Tariffs **3.0TD** and **6.1TD**) and calculate automated capacitor banks with detuned harmonic filters, in compliance with **Spanish CNMC Circular 3/2020** and **Royal Decree 1164/2001**.

👉 **Live Production URL:** [https://optivolt.streamlit.app](https://optivolt.streamlit.app)

---

## 🏭 Industrial Problem Solved
Small and medium industrial facilities (metalworking workshops, plastic injection plants, refrigerated logistics warehouses) in Spain continuously overpay on electricity bills due to two factors:
1. **Oversized Contracted Power:** Plant managers contract excessive capacity across periods P1 to P6 to avoid breaker tripping, unaware of the mathematical envelope imposed by the non-decreasing BOE constraint ($P_1 \le P_2 \le P_3 \le P_4 \le P_5 \le P_6$).
2. **Reactive Power Penalties:** Inductive loads (asynchronous motors, welders, transformers) lower the plant power factor ($\cos \varphi < 0.95$), triggering heavy monthly utility surcharges.

## ⚡ Technical Features
- **Monotonic Optimization Algorithm:** Balances peak recorded demand (maximeters) respecting the CNMC mathematical constraints.
- **Reactive & Harmonic Engineering:** Computes required capacitor reactive capacity ($Q_c$) with **189 Hz ($p = 7\%$) detuned reactor specifications** to prevent 5th harmonic resonance.
- **3-Page Official Expert Dossier:** Generates a complete engineering report and legal claim letter citing Electricity Sector Act 24/2013 ready for distribution utilities (Iberdrola, Endesa, Naturgy, etc.).
- **Stripe B2B Checkout:** End-to-end payment processing and cryptographic session token verification.
- **Bilingual Interface:** Full support for both Spanish (`🇪🇸 ES`) and English (`🇬🇧 EN`).

## 🛠️ Tech Stack
- **Engine:** Python 3.10+, Pandas, NumPy
- **Interface:** Streamlit (Custom Executive Slate UI)
- **Data Visualization:** Plotly Graph Objects
- **Billing API:** Stripe Python SDK

---
Developed by **Alberto Lantarón**  
*Industrial Engineering & Applied Software Solutions*
