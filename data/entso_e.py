import os
from dotenv import load_dotenv
from entsoe import EntsoePandasClient
import pandas as pd
import streamlit as st

load_dotenv()

def get_greek_day_ahead_prices(start: str, end: str) -> pd.Series:
    """
    Παίρνει ωριαίες day-ahead τιμές για την Ελλάδα (GR zone).
    """
    API_TOKEN = st.secrets["ENTSO_E_TOKEN"]
    client = EntsoePandasClient(api_key=API_TOKEN)
    
    start_ts = pd.Timestamp(start, tz="Europe/Athens")
    end_ts   = pd.Timestamp(end,   tz="Europe/Athens")
    
    prices = client.query_day_ahead_prices(
        country_code="GR",
        start=start_ts,
        end=end_ts
    )
    
    return prices