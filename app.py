from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import time

app = Flask(__name__)
CORS(app)

# Cache system - 15 minutes
cache = {}
CACHE_TIME = 900

# Nifty 500 stocks
NIFTY500_STOCKS = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","BHARTIARTL",
    "SBIN","INFY","LICI","ITC","HINDUNILVR","LT","BAJFINANCE",
    "HCLTECH","MARUTI","SUNPHARMA","ADANIENT","KOTAKBANK","TITAN",
    "ONGC","NTPC","TECHM","WIPRO","ULTRACEMCO","AXISBANK","POWERGRID",
    "BAJAJFINSV","NESTLEIND","COALINDIA","M&M","ADANIPORTS",
    "TATAMOTORS","JSWSTEEL","TATASTEEL","DRREDDY","APOLLOHOSP",
    "HINDALCO","GRASIM","CIPLA","EICHERMOT","BPCL","HEROMOTOCO",
    "DIVISLAB","TATACONSUM","SBILIFE","BRITANNIA","HDFCLIFE",
    "INDUSINDBK","BAJAJ-AUTO","VEDL","SHREECEM","ICICIGI",
    "PIDILITIND","HAVELLS","DABUR","MARICO","BERGEPAINT",
    "GODREJCP","MUTHOOTFIN","LUPIN","TORNTPHARM","BIOCON",
    "AUROPHARMA","ALKEM","IPCALAB","ABBOTINDIA","SIEMENS",
    "ABB","BOSCHLTD","CUMMINSIND","THERMAX","VOLTAS",
    "BLUESTARCO","BATAINDIA","PAGEIND","TRENT","DMART",
    "NYKAA","ZOMATO","IRCTC","INDIGO","TATAPOWER",
    "TORNTPOWER","NHPC","SJVN","PFC","RECLTD",
    "IRFC","BANKBARODA","PNB","CANBK","UNIONBANK",
    "INDIANB","FEDERALBNK","IDFCFIRSTB","BANDHANBNK","RBLBANK",
    "CHOLAFIN","M&MFIN","SUNDARMFIN","SHRIRAMFIN","LICHSGFIN",
    "PERSISTENT","MPHASIS","LTIM","COFORGE","KPITTECH",
    "TATAELXSI","DIXON","ESCORTS","ASHOKLEY","TVSMOTOR",
    "MOTHERSON","APOLLOTYRE","CEATLTD","BALKRISIND","EXIDEIND",
    "HINDPETRO","IOC","GAIL","PETRONET","SAIL",
    "NMDC","UPL","PIIND","RALLIS","ASTRAL",
    "SUPREMEIND","AARTIIND","DEEPAKNI","DALBHARAT","JKCEMENT",
    "RAMCOCEM","GODREJPROP","DLF","OBEROIRLTY","PRESTIGE",
    "BRIGADE","PHOENIXLTD","SOBHA"
]

def get_cache(key):
    if key in cache:
        if time.time() - cache[key]['time'] < CACHE_TIME:
            return cache[key]['data']
    return None

def set_cache(key, data):
    cache[key] = {'data': data, 'time': time.time()}

@app.route('/')
def home():
    return jsonify({
        "status": "MITS 360 Scanner API Running ✅",
        "version": "1.0",
        "scanners": {
            "52_week_breakout": "/api/52week-breakout"
        }
    })

@app.route('/api/52week-breakout')
def week52_breakout():
    cached = get_cache('52week')
    if cached:
        return jsonify(cached)

    results = []

    for symbol in NIFTY500_STOCKS:
        try:
            ticker = symbol + ".NS"
            df = yf.download(ticker, period="52wk", interval="1d", progress=False)

            if df.empty or len(df) < 50:
                continue

            week52_high = float(df['High'].max())
            current_price = float(df['Close'].iloc[-1])

            # Volume check
            avg_volume = float(df['Volume'].iloc[-20:].mean())
            today_volume = float(df['Volume'].iloc[-1])
            volume_ratio = round(today_volume / avg_volume, 2) if avg_volume > 0 else 0

            # Breakout condition: within 2% of 52W high + volume 1.5x
            near_high = current_price >= week52_high * 0.98

            if near_high and volume_ratio >= 1.5:
                breakout_pct = round(((current_price - week52_high) / week52_high) * 100, 2)
                results.append({
                    "symbol": symbol,
                    "cmp": round(current_price, 2),
                    "week52_high": round(week52_high, 2),
                    "breakout_pct": breakout_pct,
                    "volume_ratio": volume_ratio,
                    "signal": "🚀 Breakout" if current_price >= week52_high else "⚡ Near Breakout"
                })

        except Exception:
            continue

    results.sort(key=lambda x: x['volume_ratio'], reverse=True)

    response = {
        "status": "success",
        "count": len(results),
        "last_updated": time.strftime("%d-%m-%Y %H:%M:%S"),
        "data": results,
        "note": "52-Week High Breakout with Volume Confirmation (1.5x avg)"
    }

    set_cache('52week', response)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
