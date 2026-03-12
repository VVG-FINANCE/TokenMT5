import streamlit as st
import requests
import time

def get_price():
    # Usando a API gratuita e sem chave da ExchangeRate-API
    # É muito mais amigável com servidores de cloud
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates']['USD'], "Open-ER-API"
    except Exception as e:
        return None, str(e)

st.set_page_config(page_title="Debug Final", layout="wide")
st.title("📟 Sniper Debug Engine")

price, source = get_price()

if price:
    st.metric("PREÇO EUR/USD", f"{price:.5f}")
    st.success(f"Fonte Ativa: {source}")
else:
    st.error(f"Falha na conexão: {source}")

if st.button("Rerun"):
    st.rerun()

time.sleep(2)
st.rerun()
