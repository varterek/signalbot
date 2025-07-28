import ccxt
import pandas as pd
import time
from datetime import datetime, timezone
import requests
import ta
import signal
import sys

# Webhooki Discord
WEBHOOK_5MIN = "https://discord.com/api/webhooks/1399045854047899778/CufeEo3yzitkpgi4CDhUy18ZAwopoYbueqqCWSML73dFR8K89AxhtxiVBJDleI8tIDVh"
WEBHOOK_15MIN = "https://discord.com/api/webhooks/1399045974902571230/tx9oQTlTd_tldIQ49AEw057Oy3IlaSy6ohVxVnoRibm-fVcfPvY-LR_dn77vwHDb3Ab4"
WEBHOOK_HEARTBEAT = "https://discord.com/api/webhooks/1399063988410777653/DOgJlVycpgLut0MeZBvjGxHmgsE-IKhB9XlnNOS82vzVPc5lAuLmvi65ERS6Ql8gKOPG"  # === HEARTBEAT

# Inicjalizacja API MEXC
exchange = ccxt.mexc({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Pobierz wszystkie symbole futures z MEXC
def get_all_futures_symbols():
    try:
        markets = exchange.load_markets()
        return [symbol for symbol, m in markets.items() if m.get('contract', False) and m.get('active', True)]
    except Exception as e:
        print(f"Błąd pobierania symboli futures: {e}")
        return []

# Ustaw wybrane symbole futures
symbols = [
    "DOGE/USDT", "PEPE/USDT", "XRP/USDT", "PENGU/USDT", "SUI/USDT", "BTC/USDT", "ETH/USDT", "SOL/USDT",
    "VINE/USDT", "AVAX/USDT", "WIF/USDT", "ENA/USDT", "BNB/USDT", "LTC/USDT", "OP/USDT", "AERO/USDT",
    # "CHF/USDT", "1000BONK/USDT", "MATIC/USDT"
    "WLD/USDT", "LINK/USDT", "XLM/USDT", "ADA/USDT", "DOT/USDT"
]

def send_discord_message(msg):
    for webhook in [WEBHOOK_5MIN, WEBHOOK_15MIN]:
        try:
            response = requests.post(webhook, json={"content": msg})
            print(f"Wysyłanie wiadomości do webhooka {webhook}: status {response.status_code}")
        except Exception as e:
            print(f"Błąd podczas wysyłania do webhooka {webhook}: {e}")

def send_discord_signal(symbol, signal_type, interval, color):
    webhook = WEBHOOK_5MIN if interval == '5m' else WEBHOOK_15MIN
    color_emoji = {
        "yellow": "🟡",
        "green": "🟢",
        "blue": "🔵"
    }.get(color, "🔔")
    # Dodaj czas lokalny (Polska) obok UTC
    utc_now = datetime.now(timezone.utc)
    pl_now = utc_now.astimezone(timezone(tzinfo=None, name="Europe/Warsaw")) if hasattr(timezone, 'tzinfo') else pd.Timestamp.utcnow().tz_localize('UTC').tz_convert('Europe/Warsaw')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    pl_str = pl_now.strftime('%Y-%m-%d %H:%M:%S Polska')
    # Dodaj oznaczenie roli do sygnałów niebieskich
    mention = " <@&1399417046176890982>" if color == "blue" else ""
    content = f"{color_emoji} {signal_type} sygnał na `{symbol}` – interwał {interval} – {utc_str} / {pl_str}{mention}"
    try:
        response = requests.post(webhook, json={"content": content})
        print(f"Wysłano {color} sygnał {signal_type} dla {symbol} na {interval}: status {response.status_code}")
    except Exception as e:
        print(f"Błąd wysyłania sygnału do webhooka {webhook}: {e}")

def send_heartbeat():  # === HEARTBEAT
    try:
        utc_now = datetime.now(timezone.utc)
        # Poprawne pobranie czasu polskiego niezależnie od wersji Pythona/pandas
        try:
            import pytz
            pl_tz = pytz.timezone("Europe/Warsaw")
            pl_now = utc_now.astimezone(pl_tz)
        except ImportError:
            pl_now = pd.Timestamp(utc_now).tz_convert('Europe/Warsaw')
        utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
        pl_str = pl_now.strftime('%Y-%m-%d %H:%M:%S PL TIME')
        content = f"✅ ESRW Signalbot działa – {pl_str}"
        response = requests.post(WEBHOOK_HEARTBEAT, json={"content": content})
        print(f"Heartbeat wysłany: status {response.status_code}")
    except Exception as e:
        print(f"Błąd podczas wysyłania heartbeat: {e}")

def fetch_ohlcv(symbol, timeframe, limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv or len(ohlcv) == 0:
            print(f"Brak danych OHLCV dla {symbol} na {timeframe}")
            return None
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Błąd pobierania danych dla {symbol} na {timeframe}: {e}")
        return None

import ta.momentum
def detect_signal(df, symbol, interval):
    if df is None or len(df) < 50:
        return None, None

    # EMA
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()

    # Stochastic RSI (zakres 0–1)
    stoch_rsi = ta.momentum.StochRSIIndicator(close=df['close'], window=14, smooth1=3, smooth2=3)
    df['stoch_k'] = stoch_rsi.stochrsi_k()
    df['stoch_d'] = stoch_rsi.stochrsi_d()

    last = df.iloc[-1]

    # ---- WARUNKI LONG ----
    long_price_cond = (
        last['close'] > last['ema20'] and
        last['close'] > last['ema50'] and
        last['ema20'] > last['ema50']
    )
    long_stoch_cond = (
        last['stoch_k'] > last['stoch_d'] and
        last['stoch_k'] < 0.20 and
        last['stoch_d'] < 0.20
    )
    long_cond = long_price_cond and long_stoch_cond

    # ---- WARUNKI SHORT ----
    short_price_cond = (
        last['close'] < last['ema20'] and
        last['close'] < last['ema50'] and
        last['ema20'] < last['ema50']
    )
    short_stoch_cond = (
        last['stoch_k'] < last['stoch_d'] and
        last['stoch_k'] > 0.80 and
        last['stoch_d'] > 0.80
    )
    short_cond = short_price_cond and short_stoch_cond

    # ---- WARUNEK WOLUMENU (do uzupełnienia) ----
    # Dla long: wolumen rośnie na zielonych świecach (close > open, volume > poprzedni volume)
    # Dla short: wolumen rośnie na czerwonych świecach (close < open, volume > poprzedni volume)
    prev = df.iloc[-2]
    long_volume_cond = (last['close'] > last['open']) and (last['volume'] > prev['volume'])
    short_volume_cond = (last['close'] < last['open']) and (last['volume'] > prev['volume'])
    volume_condition_long = long_volume_cond
    volume_condition_short = short_volume_cond

    # ---- SYGNAŁ ŻÓŁTY (do wprowadzenia później) ----
    # yellow_condition = False

    print(f"[{symbol} {interval}] Close: {last['close']:.2f}, EMA20: {last['ema20']:.2f}, EMA50: {last['ema50']:.2f}")
    print(f"StochRSI K: {last['stoch_k']:.2f}, D: {last['stoch_d']:.2f}, Long: {long_cond}, Short: {short_cond}")
    print(f"Volume: {last['volume']:.2f}, Prev Volume: {prev['volume']:.2f}, LongVol: {volume_condition_long}, ShortVol: {volume_condition_short}")

    # Niebieski: warunki zielone + wolumen
    if long_cond and volume_condition_long:
        return "LONG", "blue"
    if short_cond and volume_condition_short:
        return "SHORT", "blue"
    # Zielony: obecne warunki
    if long_cond:
        return "LONG", "green"
    if short_cond:
        return "SHORT", "green"
    # Żółty: do wprowadzenia później
    # if yellow_condition:
    #     return "LONG", "yellow"
    return None, None

def run(interval, force=False):
    now = datetime.now(timezone.utc)
    if not force:
        if interval == '5m' and now.minute % 5 != 0:
            return
        if interval == '15m' and now.minute % 15 != 0:
            return

    for symbol in symbols:
        df = fetch_ohlcv(symbol, interval)
        signal_type, color = detect_signal(df, symbol, interval)
        if signal_type and color:
            send_discord_signal(symbol, signal_type, interval, color)
        else:
            print(f"Sprawdzono sygnał dla {symbol} na interwale {interval} – Nie znaleziono")

def on_exit(signum=None, frame=None):
    print("Zamykanie bota, wysyłam komunikat o przerwaniu...")
    try:
        send_discord_message("❌ ESRW Signalbot został przerwany.")
        # Daj czas na wysłanie wiadomości zanim proces się zakończy
        time.sleep(2)
    except Exception as e:
        print(f"Błąd podczas wysyłania komunikatu o przerwaniu: {e}")
    finally:
        sys.exit(0)

def main():
    print("Uruchamiam ESRW Signalbot...")
    send_discord_message("✅ ESRW Signalbot uruchomiony.")

    # Obsługa Ctrl+C i SIGTERM
    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    last_heartbeat = time.time()

    try:
        run('5m', force=True)
        run('15m', force=True)
        send_heartbeat()  # pierwsze odpalenie

        while True:
            run('5m')
            run('15m')

            # === HEARTBEAT co 30 minut
            if time.time() - last_heartbeat >= 1800:
                send_heartbeat()
                last_heartbeat = time.time()

            time.sleep(60)
    except Exception as e:
        print(f"Wyjątek główny: {e}")
        on_exit()
    finally:
        on_exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Wyjątek poza main(): {e}")
        on_exit()
