
import time
import requests
import ccxt
import pandas as pd
import ta
from datetime import datetime

WEBHOOK_5MIN = "https://discord.com/api/webhooks/1399045854047899778/CufeEo3yzitkpgi4CDhUy18ZAwopoYbueqqCWSML73dFR8K89AxhtxiVBJDleI8tIDVh"
WEBHOOK_15MIN = "https://discord.com/api/webhooks/1399045974902571230/tx9oQTlTd_tldIQ49AEw057Oy3IlaSy6ohVxVnoRibm-fVcfPvY-LR_dn77vwHDb3Ab4"

symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 'OP/USDT:USDT']
exchange = ccxt.mexc({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def fetch_ohlcv(symbol, timeframe):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)

    stoch_rsi = ta.momentum.StochRSIIndicator(close=df['close'], window=14, smooth1=3, smooth2=3)
    df['stoch_k'] = stoch_rsi.stochrsi_k()
    df['stoch_d'] = stoch_rsi.stochrsi_d()

    return df

def detect_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Warunki LONG
    if (
        prev['close'] < prev['ema20'] and prev['close'] < prev['ema50']
        and last['close'] > last['ema20'] and last['close'] > last['ema50']
        and prev['ema20'] < prev['ema50'] and last['ema20'] > last['ema50']
        and prev['stoch_k'] < 20 and prev['stoch_d'] < 20
        and last['stoch_k'] > last['stoch_d']
        and last['close'] > last['open'] and last['volume'] > prev['volume']
    ):
        return "LONG"

    # Warunki SHORT
    if (
        prev['close'] > prev['ema20'] and prev['close'] > prev['ema50']
        and last['close'] < last['ema20'] and last['close'] < last['ema50']
        and prev['ema20'] > prev['ema50'] and last['ema20'] < last['ema50']
        and prev['stoch_k'] > 80 and prev['stoch_d'] > 80
        and last['stoch_k'] < last['stoch_d']
        and last['close'] < last['open'] and last['volume'] > prev['volume']
    ):
        return "SHORT"

    return None

def send_discord_signal(symbol, signal, interval):
    webhook = WEBHOOK_5MIN if interval == '5m' else WEBHOOK_15MIN
    message = {
        "content": f"🔔 **{signal} sygnał** na `{symbol}` – interwał **{interval}** – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    requests.post(webhook, json=message)

def run(interval):
    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, interval)
            df = calculate_indicators(df)
            signal = detect_signal(df)
            if signal:
                send_discord_signal(symbol.split(':')[0], signal, interval)
        except Exception as e:
            print(f"Błąd dla {symbol}: {e}")

while True:
    now = datetime.utcnow()
    if now.minute % 5 == 0:
        run('5m')
    if now.minute % 15 == 0:
        run('15m')
    time.sleep(60)
