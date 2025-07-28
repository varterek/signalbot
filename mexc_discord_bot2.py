import ccxt
import pandas as pd
import time
from datetime import datetime, timezone
import requests
import ta
import signal
import sys

# Webhooki Discord
WEBHOOK_5MIN = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"
WEBHOOK_15MIN = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"
WEBHOOK_HEARTBEAT = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"  # === HEARTBEAT

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

# Usuń ręczne ustawianie symboli futures
# symbols = ["BTCUSDT", "ETHUSDT", ...]  # <-- USUŃ TĘ LINIĘ JEŚLI ISTNIEJE

# Webhooki Discord
WEBHOOK_5MIN = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"
WEBHOOK_15MIN = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"
WEBHOOK_HEARTBEAT = "https://discord.com/api/webhooks/1399427839513591828/18mcZ0xr1WQ1gayS5p4nfvUFHPdQZ_DTesAMQzosW5Nt20PDW1KpYHBvxcy5IDQtraka"  # === HEARTBEAT

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

def send_discord_message(msg):
    for webhook in [WEBHOOK_5MIN, WEBHOOK_15MIN]:
        try:
            response = requests.post(webhook, json={"content": msg})
            print(f"Wysyłanie wiadomości do webhooka {webhook}: status {response.status_code}")
        except Exception as e:
            print(f"Błąd podczas wysyłania do webhooka {webhook}: {e}")

def send_discord_signal(symbol, signal_type, interval, color, last=None, conds=None):
    webhook = WEBHOOK_5MIN if interval == '5m' else WEBHOOK_15MIN
    color_emoji = {
        "yellow": "🟡",
        "green": "🟢",
        "blue": "🔵",
        "purple": "🟣"
    }.get(color, "🔔")
    utc_now = datetime.now(timezone.utc)
    try:
        import pytz
        pl_tz = pytz.timezone("Europe/Warsaw")
        pl_now = utc_now.astimezone(pl_tz)
    except ImportError:
        pl_now = pd.Timestamp.utcnow().tz_convert('Europe/Warsaw')
    utc_str = utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')
    pl_str = pl_now.strftime('%Y-%m-%d %H:%M (Europe/Warsaw)')
    mention = " <@&1399417046176890982>" if color == "blue" else ""
    # --- EMBED dla niebieskiego sygnału ---
    if color == "blue" and last is not None:
        # Przygotuj link do MEXC
        # symbol może być np. VVAIFU/USDT:USDT lub VIRTUAL/USDT
        base = symbol.split('/')[0]
        quote = "USDT"
        mexc_symbol = f"{base}_{quote}"
        mexc_url = f"https://www.mexc.com/futures/{mexc_symbol}"
        embed = {
            "title": f"{color_emoji} **{signal_type}** sygnał na {symbol}",
            "url": mexc_url,  # tytuł embeda jest klikalny
            "description": (
                f"**Sygnał:** `{signal_type}`\n"
                f"**Cena:** `{last['close']}`\n"
                f"**Interwał:** `{interval}`\n"
                f"**Moment sygnału:** `{pl_str}`"
            ),
            "color": 3447003 if signal_type == "LONG" else 15158332,  # niebieski/zielony
            "footer": {
                "text": "Zobacz na MEXC",
                "icon_url": "https://www.amberdata.io/hs-fs/hubfs/MEXC_logo.png?width=480&name=MEXC_logo.png"
            }
        }
        data = {
            "content": mention,
            "embeds": [embed]
        }
        try:
            response = requests.post(webhook, json=data)
            print(f"Wysłano {color} sygnał {signal_type} (embed) dla {symbol} na {interval}: status {response.status_code}")
        except Exception as e:
            print(f"Błąd wysyłania sygnału (embed) do webhooka {webhook}: {e}")
        return
    # --- Pozostałe sygnały ---
    content = f"{color_emoji} **{signal_type}** sygnał na `{symbol}` – interwał {interval} – {pl_str} {mention}"
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
        return None, None, None, None

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

    # ---- WARUNEK WOLUMENU ----
    prev = df.iloc[-2]
    long_volume_cond = (last['close'] > last['open']) and (last['volume'] > prev['volume'])
    short_volume_cond = (last['close'] < last['open']) and (last['volume'] > prev['volume'])
    volume_condition_long = long_volume_cond
    volume_condition_short = short_volume_cond

    # ---- WARUNEK OPÓR/WSPARCIE (fioletowy) ----
    # LONG: close przebija najwyższy high z ostatnich 10 świec (bez bieżącej)
    # SHORT: close przebija najniższy low z ostatnich 10 świec (bez bieżącej)
    resistance = df['high'][-11:-1].max()
    support = df['low'][-11:-1].min()
    long_breakout = last['close'] > resistance
    short_breakdown = last['close'] < support

    print(f"[{symbol} {interval}] Close: {last['close']:.2f}, EMA20: {last['ema20']:.2f}, EMA50: {last['ema50']:.2f}")
    print(f"StochRSI K: {last['stoch_k']:.2f}, D: {last['stoch_d']:.2f}, Long: {long_cond}, Short: {short_cond}")
    print(f"Volume: {last['volume']:.2f}, Prev Volume: {prev['volume']:.2f}, LongVol: {volume_condition_long}, ShortVol: {volume_condition_short}")
    print(f"Resistance (10): {resistance:.2f}, Support (10): {support:.2f}, LongBreakout: {long_breakout}, ShortBreakdown: {short_breakdown}")

    # Fioletowy: wszystkie warunki + breakout/breakdown
    if long_cond and volume_condition_long and long_breakout:
        return "LONG", "purple", None, [long_price_cond, long_stoch_cond, long_volume_cond, long_breakout]
    if short_cond and volume_condition_short and short_breakdown:
        return "SHORT", "purple", None, [short_price_cond, short_stoch_cond, short_volume_cond, short_breakdown]
    # Niebieski: warunki zielone + wolumen
    if long_cond and volume_condition_long:
        return "LONG", "blue", last, [long_price_cond, long_stoch_cond, long_volume_cond, True]
    if short_cond and volume_condition_short:
        return "SHORT", "blue", last, [short_price_cond, short_stoch_cond, short_volume_cond, True]
    # Zielony: obecne warunki
    if long_cond:
        return "LONG", "green", None, None
    if short_cond:
        return "SHORT", "green", None, None
    # Żółty: do wprowadzenia później
    # if yellow_condition:
    #     return "LONG", "yellow", None, None
    return None, None, None, None

def run(interval, force=False):
    now = datetime.now(timezone.utc)
    if not force:
        if interval == '5m' and now.minute % 5 != 0:
            return
        if interval == '15m' and now.minute % 15 != 0:
            return

    # Użyj dynamicznie pobranych symboli
    for symbol in symbols:
        df = fetch_ohlcv(symbol, interval)
        signal_type, color, last, conds = detect_signal(df, symbol, interval)
        if signal_type and color:
            send_discord_signal(symbol, signal_type, interval, color, last, conds)
        else:
            print(f"Sprawdzono sygnał dla {symbol} na interwale {interval} – Nie znaleziono")

def on_exit(signum=None, frame=None):
    print("Zamykanie bota, wysyłam komunikat o przerwaniu...")
    try:
        send_discord_message("❌ ESRW Signalbot został przerwany. Napotkano blad. ")
        # Daj czas na wysłanie wiadomości zanim proces się zakończy
        time.sleep(2)
    except Exception as e:
        print(f"Błąd podczas wysyłania komunikatu o przerwaniu: {e}")
    finally:
        sys.exit(0)

def main():
    print("Uruchamiam ESRW Signalbot...")
    send_discord_message("✅ ESRW Signalbot uruchomiony.")

    # Pobierz wszystkie symbole futures z MEXC na starcie
    global symbols
    symbols = get_all_futures_symbols()
    print(f"Załadowano {len(symbols)} symboli futures z MEXC.")

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
    finally:
        on_exit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Wyjątek poza main(): {e}")
        on_exit()
