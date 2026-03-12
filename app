import streamlit as st
import numpy as np
import yfinance as yf
import requests
import time
from collections import deque

# --- CONFIGURAÇÃO ---
ALPHA = 0.2  # Peso da nova leitura (quanto menor, mais suave o preço)

class SniperCore:
    def __init__(self):
        self.stream = deque([1.15]*500, maxlen=500)
        self.current_tick = 1.15

    def get_market_consensus(self):
        """Consulta todas as fontes e retorna a mediana suavizada"""
        prices = []
        
        # 1. YFinance
        try:
            yf_p = float(yf.Ticker("EURUSD=X").fast_info['last_price'])
            prices.append(yf_p)
        except: pass
        
        # 2. Open.er-api
        try:
            er_p = float(requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2).json()['rates']['USD'])
            prices.append(er_p)
        except: pass
        
        # 3. Frankfurter
        try:
            frk_p = float(requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2).json()['rates']['USD'])
            prices.append(frk_p)
        except: pass

        if prices:
            # Mediana para evitar discrepâncias (outliers)
            raw_median = np.median(prices)
            # Suavização Exponencial: Preço Final = (ALPHA * Novo) + ((1-ALPHA) * Anterior)
            self.current_tick = (ALPHA * raw_median) + ((1 - ALPHA) * self.current_tick)
            
        self.stream.append(self.current_tick)
        return self.current_tick, len(prices)

# --- INTERFACE ---
st.set_page_config(page_title="Sniper Core Aggregator", layout="wide")
st.title("🎯 Sniper Core: Agregação Consensual")

@st.cache_resource
def init_sniper():
    return SniperCore()

sniper = init_sniper()

metric_ph = st.empty()
chart_ph = st.empty()

while True:
    price, active_sources = sniper.get_market_consensus()
    
    
    
    with metric_ph.container():
        col1, col2 = st.columns(2)
        col1.metric("Preço Consensual (EUR/USD)", f"{price:.5f}")
        col2.metric("Fontes Ativas", f"{active_sources}/3")
        
    chart_ph.line_chart(list(sniper.stream)[-100:])
    
    time.sleep(2)
    st.rerun()
