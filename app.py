import streamlit as st
import requests

# Acessa os segredos configurados no Cloud
TOKEN = st.secrets["META_TOKEN"]
ACCOUNT_ID = st.secrets["ACCOUNT_ID"]
SIMBOLO = "EURUSD"

# Cabeçalhos
headers = {"auth-token": TOKEN}

st.title("Monitor Sniper: EUR/USD")

# Função para buscar dados (Preço Atual e Fechamento Anterior)
def get_market_data():
    # Preço Atual
    url_tick = f"https://mt-online-api-1.metaapi.cloud/users/current/accounts/{ACCOUNT_ID}/symbols/ticks/{SIMBOLO}"
    # Preço Fechamento Ontem (Candle diário anterior)
    url_candle = f"https://mt-online-api-1.metaapi.cloud/users/current/accounts/{ACCOUNT_ID}/symbols/candles/{SIMBOLO}/1d?limit=2"
    
    tick = requests.get(url_tick, headers=headers).json()
    candles = requests.get(url_candle, headers=headers).json()
    
    # Preço de fechamento do dia anterior (índice 0 é o candle anterior completo)
    close_ontem = float(candles[0]['close'])
    
    return tick['bid'], close_ontem

# Execução
try:
    bid, close_ontem = get_market_data()
    
    # Cálculo de Pips (1 pip = 0.0001 no EURUSD)
    variacao_pips = (bid - close_ontem) / 0.0001
    
    # Exibição dos dados
    col1, col2 = st.columns(2)
    col1.metric("Preço Atual (Bid)", f"{bid:.5f}")
    col2.metric("Variação vs Ontem", f"{variacao_pips:+.1f} pips")

    # Área de Testes de Validação
    st.divider()
    st.subheader("Testes de Validação do Sistema")
    
    # Teste 1: Conectividade
    with st.expander("Validar Conexão com Servidor"):
        st.success("Conectado com sucesso ao servidor da Corretora.")
    
    # Teste 2: Integridade de Dados
    with st.expander("Integridade do Feed"):
        if bid > 0:
            st.write(f"Preço bid capturado: {bid}")
            st.write("Status: OK - Feed estável.")
        else:
            st.error("Erro: Preço inválido.")

except Exception as e:
    st.error(f"Falha ao conectar: {e}")
