# sniper_core_mt5.py
import numpy as np
import requests
import yfinance as yf
from collections import deque
from fastapi import FastAPI
from pydantic import BaseModel
from threading import Thread
import time
import random

# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================
ALPHA = 0.2               # peso do preço novo na reancoragem
WINDOW_HISTORY = 50       # janela histórica para reconstrução
TRAJECTORIES = 100        # Monte Carlo
VOL_FACTOR = 0.05         # volatilidade relativa
STREAM_LEN = 500          # histórico de ticks
MICROTICK_MIN = 0.00002   # microflutuação mínima
MICROTICK_MAX = 0.00008   # microflutuação máxima
TICK_INTERVAL_MIN = 0.3   # segundos
TICK_INTERVAL_MAX = 1.0

# ==========================================
# MOTOR DE PREÇOS
# ==========================================
class SniperCore:
    def __init__(self):
        # Inicializa histórico com preço real se possível
        last_price = self.get_initial_price()
        self.stream = deque([last_price]*STREAM_LEN, maxlen=STREAM_LEN)
        self.current_tick = last_price
        self.is_reliable = True
        self.errors = []
        self.market_data = {}

    def get_initial_price(self):
        """Tenta pegar preço inicial real, senão fallback 1.15"""
        try:
            price = float(yf.Ticker("EURUSD=X").fast_info['last_price'])
            return price
        except:
            return 1.15

    def fetch_consensus_price(self):
        """Consulta múltiplas APIs com retry simples e cache"""
        prices = {}
        errors = []

        # YFinance
        try:
            prices["YF"] = float(yf.Ticker("EURUSD=X").fast_info['last_price'])
        except Exception as e:
            errors.append(f"YF: {e}")

        # Open.er-api
        try:
            r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=2)
            r.raise_for_status()
            prices["ER"] = float(r.json()['rates']['USD'])
        except Exception as e:
            errors.append(f"ER: {e}")

        # Frankfurter
        try:
            r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=2)
            r.raise_for_status()
            prices["FRK"] = float(r.json()['rates']['USD'])
        except Exception as e:
            errors.append(f"FRK: {e}")

        # ECB (backup)
        try:
            if prices:
                prices["ECB"] = np.median(list(prices.values()))
            else:
                prices["ECB"] = 1.15
        except Exception as e:
            errors.append(f"ECB: {e}")

        self.market_data = prices
        self.errors = errors
        return prices, errors

    def reconstruct_via_stats(self):
        history = np.array(list(self.stream)[-WINDOW_HISTORY:])
        if len(history) < 5:
            return 1.15
        mu, sigma = np.mean(history), np.std(history)
        paths = np.random.normal(mu, sigma * VOL_FACTOR, TRAJECTORIES)
        return np.mean(paths)

    def generate_tick(self):
        prices, errors = self.fetch_consensus_price()
        if prices:
            observed_p = np.median(list(prices.values()))
            base_price = (1 - ALPHA) * self.current_tick + ALPHA * observed_p
            self.is_reliable = True
        else:
            base_price = self.reconstruct_via_stats()
            self.is_reliable = False

        # Microflutuação baseada em volatilidade
        micro_variation = np.random.uniform(MICROTICK_MIN, MICROTICK_MAX) * np.random.choice([-1, 1])
        self.current_tick = base_price + micro_variation
        self.stream.append(self.current_tick)
        return self.current_tick, self.is_reliable, self.market_data, self.errors

# Instância global
sniper = SniperCore()

# ==========================================
# THREAD DE ATUALIZAÇÃO CONTÍNUA
# ==========================================
def update_sniper_loop():
    while True:
        sniper.generate_tick()
        # Intervalo variável para simular ticks reais
        time.sleep(random.uniform(TICK_INTERVAL_MIN, TICK_INTERVAL_MAX))

thread = Thread(target=update_sniper_loop, daemon=True)
thread.start()

# ==========================================
# FASTAPI
# ==========================================
app = FastAPI(title="Sniper Core MT5 API")

class TickResponse(BaseModel):
    price: float
    is_reliable: bool
    market_data: dict
    errors: list
    history: list

@app.get("/tick", response_model=TickResponse)
def get_tick():
    return TickResponse(
        price=sniper.current_tick,
        is_reliable=sniper.is_reliable,
        market_data=sniper.market_data,
        errors=sniper.errors,
        history=list(sniper.stream)[-100:]  # últimos 100 ticks
    )

# RODAR LOCAL:
# uvicorn sniper_core_mt5:app --reload
