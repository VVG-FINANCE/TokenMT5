import streamlit as st
import requests
import yfinance as yf
import numpy as np
import time

# ==========================================
# 1. ENGINE ESTATÍSTICA (RECONSTRUÇÃO)
# ==========================================
def reconstruct_price(api):
    """
    Simulação Bayesiana + Monte Carlo:
    Estima o preço futuro baseado no histórico recente.
    """
    # Extrai o histórico recente (janela de 20 períodos)
    history = np.array(api["stream"][-20:])
    
    # Bayesiano: Calcula a média móvel com peso no momento (inércia)
    mu = np.mean(history)
    sigma = np.std(history)
    
    # Monte Carlo: Gera 50 trajetórias possíveis para o próximo tick
    # O ruído é baseado na volatilidade histórica (sigma)
    paths = np.random.normal(mu, sigma * 0.1, 50)
    
    # Retorna o preço mais provável (o "ponto central" da simulação)
    return np.mean(paths)

# ==========================================
# 2. LÓGICA DE CONSENSO E ENGINE
# ==========================================
def run_sniper_engine():
    api = st.session_state.pseudo_api
    market_data = fetch_consensus_price() # (Função das 4 APIs)
    
    agora = time.time()
    
    if market_data:
        # Preço via Consenso (Mediana)
        observed_p = np.median(list(market_data.values()))
        api["current_tick"] = observed_p
        api["last_sync"] = agora
    else:
        # Lógica de Reconstrução se APIs falharem
        api["current_tick"] = reconstruct_price(api)
        st.warning("⚠️ Dados offline. Preço reconstruído via Simulação Bayesiana.")

    api["stream"].append(api["current_tick"])
    if len(api["stream"]) > 250: api["stream"].pop(0)

# 
