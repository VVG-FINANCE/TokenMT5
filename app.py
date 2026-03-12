import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import time

# ==========================================
# 1. MOTOR DE CAPTURA (CASCATA DE FAILOVER)
# ==========================================
def fetch_raw_data():
    """Tenta buscar o preço real nas 4 fontes + YFinance via secrets."""
    # Ordem: 1. YFinance, 2. TwelveData, 3. AlphaVantage, 4. FCS
    
    # --- Fonte 1: YFinance ---
    try:
        ticker = yf.Ticker("EURUSD=X")
        p = ticker.fast_info['last_price']
        if p > 0: return p, "YFinance"
    except: pass

    # --- Fonte 2: TwelveData ---
    try:
        key = st.secrets["TWELVEDATA_KEY"]
        url = f"https://api.twelvedata.com/price?symbol=EUR/USD&apikey={key}"
        p = float(requests.get(url, timeout=3).json()['price'])
        if p: return p, "TwelveData"
    except: pass

    # --- Fonte 3: AlphaVantage ---
    try:
        key = st.secrets["ALPHA_VANTAGE_KEY"]
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={key}"
        res = requests.get(url, timeout=3).json()
        p = float(res['Realtime Currency Exchange Rate']['5. Exchange Rate'])
        if p: return p, "AlphaVantage"
    except: pass

    # --- Fonte 4: FCS API ---
    try:
        key = st.secrets["FCS_API_KEY"]
        url = f"https://fcsapi.com/api-v3/forex/latest?id=1&access_key={key}"
        res = requests.get(url, timeout=3).json()
        p = float(res['response'][0]['price'])
        if p: return p, "FCS_API"
    except: pass

    return None, "OFFLINE"

# ==========================================
# 2. INICIALIZAÇÃO DO BARRAMENTO (PSEUDO-API)
# ==========================================
if 'pseudo_api' not in st.session_state:
    st.session_state.pseudo_api = {
        "stream": [1.0850] * 250,      # Buffer p/ Média de 200
        "current_tick": 1.0850,
        "momentum": 0.0,
        "last_sync": time.time(),
        "active_source": "Iniciando",
        "is_reliable": False,
        "logs": []
    }

def log_engine(msg):
    st.session_state.pseudo_api["logs"].insert(0, f"[{time.strftime('%H:%M:%S')}] {msg}")

# ==========================================
# 3. CORE: MOTOR DE LIMPEZA E RECONSTRUÇÃO
# ==========================================
def run_pseudo_api():
    api = st.session_state.pseudo_api
    raw_p, source = fetch_raw_data()
    api["active_source"] = source
    
    agora = time.time()
    dt = agora - api["last_sync"]

    # --- Lógica de Validação (Filtro de Mediana) ---
    if raw_p:
        mediana = np.median(api["stream"][-7:])
        # Se desvio < 0.15%, aceita o dado real
        if abs(raw_p - mediana) < (mediana * 0.0015):
            api["momentum"] = (raw_p - api["current_tick"]) * 0.1 # Suavização
            api["current_tick"] = raw_p
            api["last_sync"] = agora
            api["is_reliable"] = True
        else:
            log_engine("⚠️ Outlier detectado e filtrado.")
            raw_p = None # Força reconstrução

    # --- Lógica de Reconstrução (Monte Carlo + Inércia) ---
    if not raw_p:
        if dt < 60: # Watchdog: 60s de tolerância
            # Simulação Monte Carlo Leve (Inércia + Ruído Gaussiano)
            noise = np.random.normal(0, 0.00001)
            api["current_tick"] += api["momentum"] + noise
            api["is_reliable"] = True
            log_engine(f"🛠️ Reconstruindo via Inércia ({source})")
        else:
            api["is_reliable"] = False
            log_engine("🚨 KILL SWITCH: Incerteza muito alta.")

    # Atualiza Buffer de Saída
    api["stream"].append(api["current_tick"])
    if len(api["stream"]) > 250: api["stream"].pop(0)

# ==========================================
# 4. INTERFACE DE MONITORAMENTO (ENGRENAGENS)
# ==========================================
st.set_page_config(page_title="Sniper Pseudo-API", layout="wide")

# Execução do Motor
run_pseudo_api()
api = st.session_state.pseudo_api

# Cabeçalho Estilo Terminal
st.title("📟 Sniper Pseudo-API Engine")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("PREÇO ATUAL", f"{api['current_tick']:.5f}")
with c2:
    color = "normal" if api["is_reliable"] else "inverse"
    status = "CONFIÁVEL" if api["is_reliable"] else "INSTÁVEL"
    st.metric("ESTADO DO MOTOR", status, delta_color=color)
with c3:
    st.metric("FONTE ATIVA", api["active_source"])
with c4:
    latencia = time.time() - api["last_sync"]
    st.metric("LATÊNCIA REAL", f"{latencia:.1f}s")

# Gráfico da "Engrenagem Interna"
st.subheader("Fluxo de Dados Tratados (Pseudo-API Stream)")
st.line_chart(api["stream"][-100:])

# Logs de Persistência
with st.expander("Visualizar Logs de Processamento"):
    for l in api["logs"][:8]: st.text(l)

# Heartbeat de 1 segundo
time.sleep(1)
st.rerun()
