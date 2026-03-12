import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time

# ==========================================
# CONFIGURAÇÕES DA PSEUDO-API
# ==========================================
SYMBOL = "EURUSD=X"
TOLERANCIA_MEDIANA = 0.0015  # 0.15% de desvio max para o Filtro de Mediana
LIMITE_INATIVIDADE = 45      # Segundos para o Watchdog cortar o fluxo

# ==========================================
# INICIALIZAÇÃO DO BARRAMENTO DE DADOS
# ==========================================
if 'pseudo_api' not in st.session_state:
    st.session_state.pseudo_api = {
        "price_stream": [1.0850] * 250, # Buffer para Média de 200
        "current_tick": 1.0850,
        "is_reliable": False,
        "last_sync": time.time(),
        "momentum": 0.0,
        "error_log": []
    }

# ==========================================
# FUNÇÕES CORE (A LÓGICA DA PSEUDO-API)
# ==========================================

def fetch_raw_data():
    """Simula a chamada de API (Substituível por requests)"""
    try:
        ticker = yf.Ticker(SYMBOL)
        price = ticker.fast_info['last_price']
        return price, True
    except Exception as e:
        return None, False

def process_engine():
    """O Motor de Reconstrução e Limpeza"""
    raw_price, success = fetch_raw_data()
    vault = st.session_state.pseudo_api
    
    # 1. WATCHDOG: Verifica latência
    tempo_desde_ultimo_sucesso = time.time() - vault["last_sync"]
    
    if success and raw_price:
        # 2. FILTRO DE MEDIANA (Limpeza)
        mediana = np.median(vault["price_stream"][-10:])
        if abs(raw_price - mediana) < (mediana * TOLERANCIA_MEDIANA):
            vault["momentum"] = raw_price - vault["current_tick"]
            vault["current_tick"] = raw_price
            vault["last_sync"] = time.time()
            vault["is_reliable"] = True
        else:
            vault["error_log"].append(f"Outlier bloqueado: {raw_price}")
            success = False # Trata como falha para ativar a reconstrução

    # 3. RECONSTRUÇÃO (Se a API falhar ou o dado for sujo)
    if not success or tempo_desde_ultimo_sucesso > 2:
        if tempo_desde_ultimo_sucesso < LIMITE_INATIVIDADE:
            # Inércia Bayesiana + Monte Carlo Leve (100 caminhos)
            ruido = np.random.normal(0, 0.00002, 100).mean()
            vault["current_tick"] += vault["momentum"] + ruido
            vault["is_reliable"] = True # Ainda confiável pela reconstrução
        else:
            vault["is_reliable"] = False # Watchdog corta: Incerteza muito alta

    # 4. ATUALIZAÇÃO DO BUFFER (A Stream que o Analista vai ler)
    vault["price_stream"].append(vault["current_tick"])
    if len(vault["price_stream"]) > 250:
        vault["price_stream"].pop(0)

# ==========================================
# INTERFACE DE TESTE (SERÁ REMOVIDA DEPOIS)
# ==========================================
st.title("🧪 Teste da Pseudo-API Sniper")

# Executa o motor
process_engine()

# Visualização para Validação
api = st.session_state.pseudo_api

col1, col2, col3 = st.columns(3)
col1.metric("Preço Pseudo-API", f"{api['current_tick']:.5f}")
col2.metric("Status de Confiança", "✅ CONFIÁVEL" if api["is_reliable"] else "❌ INSTÁVEL")
col3.metric("Latência Real", f"{time.time() - api['last_sync']:.1f}s")

# O que o seu segundo código vai "ver"
with st.expander("Visualizar Stream de Dados (Input para Análise)"):
    st.write(pd.Series(api["price_stream"][-200:]).describe())
    st.line_chart(api["price_stream"][-100:])

# Loop de atualização
time.sleep(1)
st.rerun()
