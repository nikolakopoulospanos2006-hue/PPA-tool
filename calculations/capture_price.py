import pandas as pd
import numpy as np

def calculate_capture_price(hourly_prices: pd.Series, solar_profile: pd.Series) -> float:
    """
    Υπολογίζει το capture price του solar (VWAP).
    
    Είναι ο σταθμισμένος μέσος των spot prices κατά τις ώρες 
    που παράγει το solar — πάντα χαμηλότερος από τον flat μέσο.
    """
    
    # Reset index και για τα δύο για να ταιριάζουν
    prices = hourly_prices.reset_index(drop=True)
    weights = solar_profile.reset_index(drop=True)
    
    # Κρατάμε τις κοινές ώρες
    min_len = min(len(prices), len(weights))
    prices = prices.iloc[:min_len]
    weights = weights.iloc[:min_len]
    
    # Κρατάμε μόνο τις ώρες που παράγει το solar
    producing_hours = weights > 0
    
    prices_when_producing = prices[producing_hours]
    weights_when_producing = weights[producing_hours]
    
    capture_price = np.average(prices_when_producing, weights=weights_when_producing)
    
    return round(capture_price, 2)


def calculate_cannibalization_discount(capture_price: float, 
                                        baseload_price: float) -> float:
    """
    Υπολογίζει το cannibalization discount.
    
    Πόσο χάνει το solar λόγω του ότι παράγει όταν 
    όλοι οι άλλοι παράγουν επίσης (μεσημέρι).
    
    Output:
    - discount ως ποσοστό (π.χ. 0.15 = 15%)
    """
    if baseload_price == 0:
        return 0.0
    
    discount = (baseload_price - capture_price) / baseload_price
    return round(discount, 4)


def generate_mock_solar_profile(hours=8760) -> pd.Series:
    """
    Δημιουργεί mock solar profile για testing (ένα χρόνο, ωριαία).
    Παράγει μόνο μεταξύ 6:00-20:00, με peak στις 13:00.
    """
    production = []
    for h in range(hours):
        hour_of_day = h % 24
        if 6 <= hour_of_day <= 20:
            # Κανονική κατανομή γύρω από το μεσημέρι
            output = np.exp(-0.5 * ((hour_of_day - 13) / 3) ** 2)
        else:
            output = 0.0
        production.append(output)
    
    return pd.Series(production)


def generate_mock_prices(hours=8760, base_price=85.0) -> pd.Series:
    """
    Δημιουργεί mock hourly prices για testing.
    Προσομοιώνει υψηλότερες τιμές πρωί/βράδυ, χαμηλές μεσημέρι.
    """
    prices = []
    for h in range(hours):
        hour_of_day = h % 24
        # Peak πρωί (8-10) και βράδυ (18-21)
        if 8 <= hour_of_day <= 10 or 18 <= hour_of_day <= 21:
            price = base_price * np.random.uniform(1.1, 1.3)
        # Low μεσημέρι λόγω solar
        elif 11 <= hour_of_day <= 15:
            price = base_price * np.random.uniform(0.7, 0.9)
        else:
            price = base_price * np.random.uniform(0.9, 1.1)
        prices.append(price)
    
    return pd.Series(prices)