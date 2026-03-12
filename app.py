import streamlit as st
import pandas as pd
import numpy as np
import requests
import time

# ==========================================
# 1. FUNÇÃO DE CAPTURA EXCLUSIVA (API-ONLY)
# ==========================================
def fetch_raw_data():
    """Tenta APIs pagas/secrets exclusivamente."""
    logs = st.session_state.pseudo_api["logs"]
    
    # 1. TwelveData
    try:
        url = f"https://api.twelvedata.com/price?symbol=EUR/USD&apikey={st.secrets['TWELVEDATA_KEY']}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return float(r.json()['price']), "TwelveData"
        else: logs.insert(0, f"12Data Error {r.status_code}: {r.text[:20]}")
    except Exception as e: logs.insert(0, f"12Data Falha: {str(e)[:15]}")

    # 2. AlphaVantage
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={st.secrets['ALPHA_VANTAGE_KEY']}"
        r = requests.get(url, timeout=10).json()
        if 'Realtime Currency Exchange Rate' in r:
            return float(r['Realtime Currency Exchange Rate']['5. Exchange Rate']), "AlphaVantage"
        else: logs.insert(0, f"AV Log: {str(r)[:20]}")
    except Exception as e: logs.insert(0, f"AV Falha: {str(e)[:15]}")

    # 3. FCS API
    try:
        url = f"https://fcsapi.com/api-v3/forex/latest?id=1&access_key={st.secrets['FCS_API_KEY']}"
        r = requests.get(url, timeout=10).json()
        if r.get('status') == True:
            return float(r['response'][0]['price']), "FCS_API"
        else: logs.insert(0, f"FCS Log: {str(r)[:20]}")
    except Exception as e: logs.insert(0, f"FCS Falha: {str(e)[:15]}")

    return None, "OFFLINE"

# ==========================================
# 2. INICIALIZAÇÃO DO ESTADO
# ==========================================
if 'pseudo_api' not in st.session_state:
    st.session_state.pseudo_api = {
        "stream": [1.15] * 250, 
        "current_tick": 1.15,
        "logs": ["Sistema Iniciado (Sem YFinance)"]
    }

# ==========================================
# 3. ENGINE: EXECUÇÃO DIRETA
# ==========================================
def run_pseudo_api():
    api = st.session_state.pseudo_api
    raw_p, source = fetch_raw_data()
    
    if raw_p:
        api["current_tick"] = raw_p
        api["active_source"] = source
    else:
        api["active_source"] = "Nenhuma API respondeu"
    
    api["stream"].append(api["current_tick"])
    if len(api["stream"]) > 250: api["stream"].pop(0)

# ==========================================
# 4. INTERFACE DE DEBUG
# ==========================================
st.set_page_config(page_title="Debug Sniper", layout="wide")
run_pseudo_api()
api = st.session_state.pseudo_api

st.metric("PREÇO ATUAL", f"{api['current_tick']:.5f}")
st.metric("FONTE ATIVA", api['active_source'])

st.subheader("Logs de Diagnóstico de API")
for l in api["logs"][:15]: 
    st.text(l)

if st.button("Limpar Logs"):
    st.session_state.pseudo_api["logs"] = []
    st.rerun()

time.sleep(2)
st.rerun()
