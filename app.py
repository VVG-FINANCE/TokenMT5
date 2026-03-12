import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time

# ==========================================
# 1. FUNÇÃO DE CAPTURA COM DIAGNÓSTICO (A "PSEUDO-API")
# ==========================================
def fetch_raw_data():
    """Tenta fontes em cascata com log de erro para depuração."""
    logs = st.session_state.pseudo_api["logs"]
    
    # 1. YFinance (Não requer chave)
    try:
        ticker = yf.Ticker("EURUSD=X")
        p = ticker.fast_info['last_price']
        if p and p > 0: return p, "YFinance"
    except Exception as e:
        logs.insert(0, f"YF Falha: {str(e)[:15]}")

    # 2. TwelveData
    try:
        url = f"https://api.twelvedata.com/price?symbol=EUR/USD&apikey={st.secrets['TWELVEDATA_KEY']}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return float(r.json()['price']), "TwelveData"
        else: logs.insert(0, f"12Data Status: {r.status_code}")
    except Exception as e:
        logs.insert(0, f"12Data Falha: {str(e)[:15]}")

    # 3. AlphaVantage
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={st.secrets['ALPHA_VANTAGE_KEY']}"
        r = requests.get(url, timeout=5).json()
        if 'Realtime Currency Exchange Rate' in r:
            return float(r['Realtime Currency Exchange Rate']['5. Exchange Rate']), "AlphaVantage"
    except Exception as e:
        logs.insert(0, f"AlphaVant Falha: {str(e)[:15]}")

    # 4. FCS API
    try:
        url = f"https://fcsapi.com/api-v3/forex/latest?id=1&access_key={st.secrets['FCS_API_KEY']}"
        r = requests.get(url, timeout=5).json()
        if r.get('status') == True:
            return float(r['response'][0]['price']), "FCS_API"
    except Exception as e:
        logs.insert(0, f"FCS Falha: {str(e)[:15]}")

    return None, "OFFLINE"

# ==========================================
# 2. INICIALIZAÇÃO DO BARRAMENTO
# ==========================================
if 'pseudo_api' not in st.session_state:
    st.session_state.pseudo_api = {
        "stream": [1.15] * 250, 
        "current_tick": 1.15,
        "momentum": 0.0,
        "last_sync": time.time(),
        "active_source": "Iniciando",
        "is_reliable": False,
        "logs": []
    }

# ==========================================
# 3. ENGINE: REANCORAGEM E RECONSTRUÇÃO
# ==========================================
def run_pseudo_api():
    api = st.session_state.pseudo_api
    raw_p, source = fetch_raw_data()
    api["active_source"] = source
    
    agora = time.time()
    
    # Lógica de Reancoragem (Se o preço saltar, ele se ajusta ao real)
    if raw_p:
        diff = abs(raw_p - api["current_tick"])
        if diff > (api["current_tick"] * 0.005): # Salto > 0.5%
            api["current_tick"] = raw_p
            api["momentum"] = 0 
            api["is_reliable"] = True
            api["last_sync"] = agora
        elif diff < (api["current_tick"] * 0.002): # Dentro da tolerância
            api["momentum"] = (raw_p - api["current_tick"]) * 0.2
            api["current_tick"] = raw_p
            api["is_reliable"] = True
            api["last_sync"] = agora
        else:
            raw_p = None 

    # Motor de Reconstrução (Se não há dado)
    if not raw_p:
        if (agora - api["last_sync"]) < 60:
            noise = np.random.normal(0, 0.00001)
            api["current_tick"] += api["momentum"] + noise
            api["is_reliable"] = True
        else:
            api["is_reliable"] = False

    api["stream"].append(api["current_tick"])
    if len(api["stream"]) > 250: api["stream"].pop(0)

# ==========================================
# 4. INTERFACE E HEARTBEAT
# ==========================================
st.set_page_config(page_title="Sniper Pseudo-API", layout="wide")
run_pseudo_api()
api = st.session_state.pseudo_api

# Exibição
col1, col2 = st.columns(2)
col1.metric("PREÇO ATUAL", f"{api['current_tick']:.5f}")
col2.metric("FONTE ATIVA", api['active_source'])

st.line_chart(api["stream"][-100:])

with st.expander("Logs de Diagnóstico"):
    for l in api["logs"][:10]: st.text(l)

time.sleep(1)
st.rerun()
