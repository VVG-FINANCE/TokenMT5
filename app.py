import streamlit as st
import numpy as np
import yfinance as yf
import requests
import time
from collections import deque

# --- CONFIGURAÇÃO ---
ALPHA = 0.2  
OFFSET = -0.00300 # Ajuste interno de -190 pontos

class SniperCore:
    def __init__(self):
        self.stream = deque([1.15]*500, maxlen=500)
        self.current_tick = 1.15

    def get_market_consensus(self):
        prices = []
        try:
            # Coleta bruta das fontes
            prices.append(float(yf.Ticker("EURUSD=X").fast_info['last_price']))
            prices.append(float(requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2).json()['rates']['USD']))
            prices.append(float(requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2).json()['rates']['USD']))
        except: pass

        if prices:
            raw_median = np.median(prices)
            # Lógica interna: aplica o OFFSET para cálculo, mas o current_tick 
            # refletirá o valor já ajustado para comparação com o MT5
            adjusted_value = raw_median + OFFSET
            self.current_tick = (ALPHA * adjusted_value) + ((1 - ALPHA) * self.current_tick)
            
        self.stream.append(self.current_tick)
        return self.current_tick

# --- INTERFACE ---
st.set_page_config(page_title="Sniper Core", layout="wide")
st.title("🎯 Sniper Core MT5")

if 'sniper' not in st.session_state:
    st.session_state.sniper = SniperCore()

# Criamos containers persistentes para evitar o redesenho (piscar)
metric_placeholder = st.empty()
chart_placeholder = st.empty()

while True:
    price = st.session_state.sniper.get_market_consensus()
    
    # Atualiza a métrica dentro do placeholder sem reconstruir a página
    with metric_placeholder.container():
        st.metric("Preço de Consenso (MT5)", f"{price:.5f}")
        
    # Atualiza o gráfico no placeholder
    chart_placeholder.line_chart(list(st.session_state.sniper.stream)[-100:])
    
    time.sleep(2)
    st.rerun()
