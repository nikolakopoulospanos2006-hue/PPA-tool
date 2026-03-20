import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from calculations.capture_price import (
    calculate_capture_price,
    calculate_cannibalization_discount,
    generate_mock_solar_profile,
    generate_mock_prices
)
from calculations.strike_price import calculate_strike_price
from reports.generator import export_excel, export_pdf
from data.entso_e import get_greek_day_ahead_prices
import plotly.graph_objects as go

# ─── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="PPA Pricing Tool",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ PPA Strike Price Calculator")
st.caption("Solar Pay-as-Produced | Greek Market")

# ─── Sidebar Inputs ────────────────────────────────────────
st.sidebar.header("📥 Project Inputs")

st.sidebar.subheader("Project Details")
capacity_mw = st.sidebar.number_input("Εγκατεστημένη Ισχύς (MW)", 1.0, 500.0, 50.0)
capacity_factor = st.sidebar.slider("Capacity Factor P50 (%)", 10, 30, 19)
years = st.sidebar.slider("Διάρκεια PPA (χρόνια)", 5, 20, 12)

st.sidebar.subheader("Economics")
lcoe = st.sidebar.number_input("LCOE (€/MWh)", 20.0, 100.0, 45.0)
discount_rate = st.sidebar.slider("Discount Rate / WACC (%)", 4, 15, 7)
developer_margin = st.sidebar.slider("Developer Margin (%)", 1, 20, 5)

st.sidebar.subheader("Market Parameters")
baseload_price = st.sidebar.number_input("Baseload Market Price (€/MWh)", 30.0, 200.0, 85.0)
offtaker_discount = st.sidebar.slider("Offtaker Discount (%)", 0, 20, 10)
risk_premium = st.sidebar.number_input("Risk Premium (€/MWh)", 0.0, 20.0, 5.0)

st.sidebar.subheader("Adjustments")
indexation_rate = st.sidebar.slider("Indexation Rate (%)", 0, 5, 2)
degradation_rate = st.sidebar.slider("Panel Degradation (%/year)", 0, 2, 1)

# ─── Calculations ──────────────────────────────────────────
annual_volume = capacity_mw * (capacity_factor / 100) * 8760

# ENTSO-E Real Data
@st.cache_data
def load_real_prices():
    try:
        prices = get_greek_day_ahead_prices("20240101", "20241231")
        return prices
    except Exception as e:
        st.error(f"❌ ENTSO-E Error: {e}")
        return None


hourly_prices = load_real_prices()
solar_profile = generate_mock_solar_profile(hours=len(hourly_prices))

# Capture price από πραγματικά δεδομένα
real_capture_price = calculate_capture_price(hourly_prices, solar_profile)
real_baseload = hourly_prices.mean()

# Αναλογική προσαρμογή βάσει του baseload slider
# Αν ο χρήστης βάλει baseload 20% πάνω από το real → capture ανεβαίνει 20%
adjustment_factor = baseload_price / real_baseload
capture_price = real_capture_price * adjustment_factor


results = calculate_strike_price(
    lcoe=lcoe,
    annual_volume_mwh=annual_volume,
    discount_rate=discount_rate / 100,
    years=years,
    capture_price=capture_price,
    baseload_price=baseload_price,
    offtaker_discount=offtaker_discount / 100,
    risk_premium=risk_premium,
    developer_margin=developer_margin / 100,
    degradation_rate=degradation_rate / 100,
    indexation_rate=indexation_rate / 100,
    capacity_factor_input=capacity_factor / 100
)

# ─── Main Output ───────────────────────────────────────────
st.header("📊 Results")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎯 Proposed Strike Price",
        value=f"€{results['strike_price_proposed']} /MWh"
    )

with col2:
    st.metric(
        label="📉 Min Viable Strike (P50)",
        value=f"€{results['min_viable_strike']} /MWh"
    )

with col3:
    st.metric(
        label="⚠️ Min Viable Strike (P90)",
        value=f"€{results['min_viable_strike_p90']} /MWh"
    )

# ─── Breakdown ─────────────────────────────────────────────
st.subheader("🔍 Price Breakdown")

col4, col5 = st.columns(2)

with col4:
    st.dataframe(pd.DataFrame({
        "Component": [
            "Capture Price",
            "Baseload Price",
            "Cannibalization Discount",
            "Offtaker Discount",
            "Risk Premium",
            "Developer Margin",
        ],
        "Value": [
            f"€{results['capture_price']} /MWh",
            f"€{results['baseload_price']} /MWh",
            f"{results['cannibalization_discount_pct']}%",
            f"€{results['offtaker_discount_eur']} /MWh",
            f"€{results['risk_premium_eur']} /MWh",
            f"€{results['developer_margin_eur']} /MWh",
        ]
    }), hide_index=True)

with col5:
    st.dataframe(pd.DataFrame({
        "Parameter": [
            "Annual Volume (MWh)",
            "PPA Duration",
            "LCOE",
            "WACC",
            "Indexation Rate",
            "Degradation Rate",
        ],
        "Value": [
            f"{annual_volume:,.0f} MWh",
            f"{years} years",
            f"€{lcoe} /MWh",
            f"{discount_rate}%",
            f"{indexation_rate}%",
            f"{degradation_rate}%/year",
        ]
    }), hide_index=True)

try:
    secret_test = st.secrets["ENTSO_E_TOKEN"]
    st.write(f"Token found: {secret_test[:8]}...")
except Exception as e:
    st.error(f"Secret error: {e}")

st.success("✅ Τα δεδομένα αγοράς είναι πραγματικά — ENTSO-E Day-Ahead Prices 2024 (GR)")


# ─── Export Section ────────────────────────────────────────
st.subheader("📤 Export Report")

params = {
    "capacity_mw": capacity_mw,
    "capacity_factor": capacity_factor,
    "annual_volume": annual_volume,
    "years": years,
    "lcoe": lcoe,
    "discount_rate": discount_rate,
    "indexation_rate": indexation_rate,
    "degradation_rate": degradation_rate,
}

col_pdf, col_excel = st.columns(2)

with col_pdf:
    pdf_bytes = export_pdf(results, params)
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name=f"PPA_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )

with col_excel:
    excel_bytes = export_excel(results, params)
    st.download_button(
        label="📊 Download Excel Report",
        data=excel_bytes,
        file_name=f"PPA_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


    # ─── Sensitivity Analysis ──────────────────────────────────
st.subheader("📈 Sensitivity Analysis")

def run_sensitivity(param_name, values, base_params):
    strikes = []
    for v in values:
        p = base_params.copy()
        p[param_name] = v
        
        mock_prices = generate_mock_prices(8760, p["baseload_price"])
        mock_solar = generate_mock_solar_profile(8760)
        cap_price = calculate_capture_price(mock_prices, mock_solar)
        
        res = calculate_strike_price(
            lcoe=p["lcoe"],
            annual_volume_mwh=p["annual_volume"],
            discount_rate=p["discount_rate"] / 100,
            years=p["years"],
            capture_price=cap_price,
            baseload_price=p["baseload_price"],
            offtaker_discount=p["offtaker_discount"] / 100,
            risk_premium=p["risk_premium"],
            developer_margin=p["developer_margin"] / 100,
            degradation_rate=p["degradation_rate"] / 100,
            indexation_rate=p["indexation_rate"] / 100,
            capacity_factor_input=p["capacity_factor"] / 100,
        )
        strikes.append(res["strike_price_proposed"])
    return strikes

base_params = {
    "lcoe": lcoe,
    "annual_volume": annual_volume,
    "discount_rate": discount_rate,
    "years": years,
    "baseload_price": baseload_price,
    "offtaker_discount": offtaker_discount,
    "risk_premium": risk_premium,
    "developer_margin": developer_margin,
    "degradation_rate": degradation_rate,
    "indexation_rate": indexation_rate,
    "capacity_factor": capacity_factor,
}

sensitivity_params = {
    "lcoe":           np.linspace(lcoe * 0.7, lcoe * 1.3, 10),
    "baseload_price": np.linspace(baseload_price * 0.7, baseload_price * 1.3, 10),
    "discount_rate":  np.linspace(max(1, discount_rate - 4), discount_rate + 4, 10),
}

labels = {
    "lcoe": "LCOE (€/MWh)",
    "baseload_price": "Baseload Price (€/MWh)",
    "discount_rate": "WACC (%)",
}

colors = {
    "lcoe": "#ef4444",
    "baseload_price": "#3b82f6",
    "discount_rate": "#10b981"
}

# ── Line Chart ─────────────────────────────────────────────
st.markdown("#### 📉 Strike Price vs Παράμετροι")
fig_line = go.Figure()

for param, values in sensitivity_params.items():
    strikes = run_sensitivity(param, values, base_params)
    fig_line.add_trace(go.Scatter(
        x=list(values),
        y=strikes,
        mode="lines+markers",
        name=labels[param],
        line=dict(color=colors[param], width=2),
    ))

fig_line.update_layout(
    xaxis_title="Τιμή Παραμέτρου",
    yaxis_title="Strike Price (€/MWh)",
    legend_title="Παράμετρος",
    height=400,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Tornado Chart ──────────────────────────────────────────
st.markdown("#### 🌪️ Tornado Chart — Επίδραση στο Strike Price")

base_strike = results["strike_price_proposed"]
tornado_data = []

for param, values in sensitivity_params.items():
    strikes = run_sensitivity(param, values, base_params)
    low_impact = min(strikes) - base_strike
    high_impact = max(strikes) - base_strike
    tornado_data.append((labels[param], low_impact, high_impact))

tornado_data.sort(key=lambda x: abs(x[2] - x[1]), reverse=True)

fig_tornado = go.Figure()

for label, low, high in tornado_data:
    fig_tornado.add_trace(go.Bar(
        y=[label],
        x=[high],
        orientation="h",
        marker_color="#3b82f6",
        showlegend=False,
    ))
    fig_tornado.add_trace(go.Bar(
        y=[label],
        x=[low],
        orientation="h",
        marker_color="#ef4444",
        showlegend=False,
    ))

fig_tornado.update_layout(
    barmode="relative",
    xaxis_title="Μεταβολή Strike Price (€/MWh)",
    height=300,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
)
st.plotly_chart(fig_tornado, use_container_width=True)