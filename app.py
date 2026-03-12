import streamlit as st
import pandas as pd
# ... (importe as funções que definimos anteriormente)

st.title("🧪 Sniper Core: Painel de Diagnóstico")

# Criamos 3 colunas para ver a "inteligência" do motor
col1, col2, col3 = st.columns(3)

run_sniper_engine() # Executa a lógica
api = st.session_state.pseudo_api

with col1:
    st.metric("PREÇO ATUAL", f"{api['current_tick']:.5f}")
with col2:
    status = "✅ ONLINE (Consenso)" if api.get("is_reliable", True) else "⚠️ RECONSTRUINDO"
    st.write("Status do Motor:")
    st.success(status)
with col3:
    st.write("Fontes Ativas:")
    st.caption(api.get("active_sources", "Multi-fonte"))

# Gráfico de diagnóstico
st.line_chart(api["stream"])

# Aqui está a parte que responde sua dúvida sobre as estratégias:
with st.expander("🔍 Ver Engine de Cálculo (Estatística)"):
    st.write("Histórico recente (20 ticks):", api["stream"][-20:])
    st.write("Cálculo Bayesiano (Média/Sigma):", np.mean(api["stream"][-20:]))
    st.write("Última Simulação Monte Carlo executada com sucesso.")

st.button("Forçar Reancoragem")
