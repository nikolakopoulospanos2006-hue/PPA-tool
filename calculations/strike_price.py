import numpy as np
from scipy.optimize import brentq
from calculations.npv import calculate_npv
from calculations.capture_price import calculate_capture_price, calculate_cannibalization_discount

def calculate_strike_price(
    lcoe: float,
    annual_volume_mwh: float,
    discount_rate: float,
    years: int,
    capture_price: float,
    baseload_price: float,
    offtaker_discount: float = 0.10,
    risk_premium: float = 5.0,
    developer_margin: float = 0.05,
    degradation_rate: float = 0.005,
    indexation_rate: float = 0.02,
    capacity_factor_input: float = 0.19,
) -> dict:
    """
    Υπολογίζει το προτεινόμενο strike price ενός solar PPA.

    Inputs:
    - lcoe: κόστος παραγωγής €/MWh
    - annual_volume_mwh: εκτιμώμενη ετήσια παραγωγή MWh
    - discount_rate: WACC (π.χ. 0.07)
    - years: διάρκεια PPA
    - capture_price: VWAP solar (€/MWh)
    - baseload_price: flat μέσος market price (€/MWh)
    - offtaker_discount: έκπτωση buyer (default 10%)
    - risk_premium: πρόσθετο €/MWh για volume/basis/counterparty risk
    - developer_margin: περιθώριο κέρδους (default 5%)
    - degradation_rate: μείωση παραγωγής/έτος (default 0.5%)
    - indexation_rate: αύξηση strike price/έτος (default 2%)
    - capacity_factor_p90: P90 scenario (default 90% της P50 παραγωγής)

    Output:
    - dict με strike price και όλα τα breakdown στοιχεία
    """

    # 1. Cannibalization discount
    cannibalization_discount = calculate_cannibalization_discount(
        capture_price, baseload_price
    )

    # 2. Βρίσκουμε το minimum strike price (NPV = 0) με brentq
    def npv_equation(strike):
        return calculate_npv(
            strike_price=strike,
            lcoe=lcoe,
            annual_volume_mwh=annual_volume_mwh,
            discount_rate=discount_rate,
            years=years,
            degradation_rate=degradation_rate,
            indexation_rate=indexation_rate
        )

    # Το minimum viable strike price για τον developer
    min_strike = brentq(npv_equation, 1 , 1000)

    # Cost-based floor (καλύπτει LCOE + WACC)
    cost_based = min_strike

    # Adjustments βασισμένα στο market
    offtaker_discount_eur = min_strike * offtaker_discount
    margin_eur = min_strike * developer_margin
    cannibalization_eur = capture_price * cannibalization_discount * 0.5
    
    # CF επηρεάζει το effective LCOE άρα και το min_strike
    # CF ↓ → effective LCOE ↑ → min_strike ↑
    cf_adjustment = (0.19 / capacity_factor_input) if capacity_factor_input > 0 else 1
    adjusted_min_strike = min_strike * cf_adjustment

    # WACC adjustment — υψηλότερο WACC = υψηλότερο risk premium για τον developer
    # Reference WACC = 7%, κάθε 1% πάνω προσθέτει €1/MWh στο strike
    wacc_adjustment = (discount_rate - 0.07) * 100 * 1.0

    market_premium = max(0, capture_price - min_strike) * 0.3

    final_strike = (
        adjusted_min_strike
        + wacc_adjustment
        + market_premium
        + offtaker_discount_eur
        + risk_premium
        - cannibalization_eur
        + margin_eur
    )

    # Κάτω όριο: ποτέ κάτω από min_strike
    final_strike = max(final_strike, min_strike)

    # 4. P90 sensitivity (conservative scenario)
    p90_volume = annual_volume_mwh * 0.85 
    min_strike_p90 = brentq(
        lambda s: calculate_npv(
            strike_price=s,
            lcoe=lcoe * 1.05,  # Υποθέτουμε 5% αύξηση LCOE στο P90 λόγω χαμηλότερης παραγωγής
            annual_volume_mwh=p90_volume,
            discount_rate=discount_rate,
            years=years,
            degradation_rate=degradation_rate,
            indexation_rate=indexation_rate
        ),
        1, 1000
    )

    return {
        "strike_price_proposed": round(final_strike, 2),
        "min_viable_strike": round(min_strike, 2),
        "min_viable_strike_p90": round(min_strike_p90, 2),
        "capture_price": round(capture_price, 2),
        "baseload_price": round(baseload_price, 2),
        "cannibalization_discount_pct": round(cannibalization_discount * 100, 2),
        "offtaker_discount_eur": round(offtaker_discount_eur, 2),
        "risk_premium_eur": round(risk_premium, 2),
        "developer_margin_eur": round(margin_eur, 2),
        "indexation_rate_pct": round(indexation_rate * 100, 2),
        "degradation_rate_pct": round(degradation_rate * 100, 2),
    }