import numpy as np

def calculate_npv(strike_price, lcoe, annual_volume_mwh, discount_rate, 
                  years, degradation_rate=0.005, indexation_rate=0.02):
    """
    Υπολογίζει το NPV του PPA για τον developer.
    
    Inputs:
    - strike_price: τιμή PPA (€/MWh)
    - lcoe: κόστος παραγωγής (€/MWh)
    - annual_volume_mwh: ετήσια παραγωγή (MWh)
    - discount_rate: WACC (π.χ. 0.07 για 7%)
    - years: διάρκεια PPA
    - degradation_rate: μείωση παραγωγής ανά έτος (default 0.5%)
    - indexation_rate: αύξηση strike price ανά έτος (default 2%)
    """
    npv = 0.0
    
    for t in range(1, years + 1):
        # Παραγωγή μειώνεται λόγω panel degradation
        volume_t = annual_volume_mwh * ((1 - degradation_rate) ** t)
        
        # Strike price αυξάνεται με indexation
        strike_t = strike_price * ((1 + indexation_rate) ** t)
        
        # Cash flow = (strike - lcoe) × volume
        cash_flow = (strike_t - lcoe) * volume_t
        
        # Προεξόφληση
        npv += cash_flow / ((1 + discount_rate) ** t)
    
    return npv