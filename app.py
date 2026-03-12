import streamlit as st
import numpy as np
import yfinance as yf
import requests
import time
from collections import deque

class SniperCore:
    def __init__(self):
        self.stream = deque([1.15]*500, maxlen=500)
        self.current_tick = 1.15
        self.market_data = {}
        self.sources = ["YF", "ER", "FRK"]
        self.source_idx = 0

    def fetch_next_source(self):
        """Consulta apenas uma fonte por vez (rodízio)"""
        source = self.sources[self.source_idx]
        try:
            if source == "YF":
                price = float(yf.Ticker("EURUSD=X").fast_info['last_price'])
            elif source == "ER":
                r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2)
                price = float(r.json()['rates']['USD'])
            elif source == "FRK":
                r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2)
                price = float(r.json()['rates']['USD'])
            
            self.market_data[source] = price
            self.current_tick = price
        except Exception as e:
            st.sidebar.error(f"Erro em {source}: {e}")
        
        # Avança para a próxima fonte no próximo ciclo
        self.source_idx = (self.source_idx + 1) % len(self.sources)
        self.stream.append(self.current_tick)
        return self.current_tick, source

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Sniper Core Rodízio", layout="wide")
st.title("🎯 Sniper Core: Rodízio de APIs")

@st.cache_resource
def init_sniper():
    return SniperCore()

sniper = init_sniper()

# Placeholder para atualização dinâmica
metric_ph = st.empty()
chart_ph = st.empty()

while True:
    price, source_used = sniper.fetch_next_source()
    
    with metric_ph.container():
        col1, col2 = st.columns(2)
        col1.metric("Preço Atual (EUR/USD)", f"{price:.5f}")
        col2.info(f"Fonte ativa: **{source_used}**")
        
    chart_ph.line_chart(list(sniper.stream)[-100:])
    
    # Pausa de 2 segundos conforme solicitado
    time.sleep(2)
    st.rerun()
