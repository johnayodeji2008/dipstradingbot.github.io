from flask import Flask, jsonify, render_template
import requests
import pandas as pd
import numpy as np

app = Flask(__name__)

# Constants
API_KEY = '7b4f5957c21b4cd48f1253b8e5e7aece'
BASE_URL = 'https://api.twelvedata.com'
SYMBOL = 'BTC/USD'
INTERVAL = '15min'
MIN_RISK_REWARD_RATIO = 2

def get_live_data(symbol, interval, api_key):
    url = f"{BASE_URL}/time_series"
    params = {
        'symbol': symbol,
        'interval': interval,
        'apikey': api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    if 'values' in data:
        return pd.DataFrame(data['values'])
    else:
        raise ValueError("Error fetching data from API")

def identify_support_resistance(df):
    support = df['low'].rolling(window=20).min()
    resistance = df['high'].rolling(window=20).max()
    return support, resistance

def smc_strategy(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    
    df['prev_close'] = df['close'].shift(1)
    df['market_structure'] = np.where(df['close'] > df['prev_close'], 'Bullish', 'Bearish')
    
    support, resistance = identify_support_resistance(df)
    df['support'] = support
    df['resistance'] = resistance
    
    df['breaker'] = df['close'] > df['resistance'].shift(1)
    
    df['entry'] = np.nan
    df['take_profit'] = np.nan
    df['stop_loss'] = np.nan
    df['risk_to_reward'] = np.nan

    for i in range(1, len(df)):
        if df.loc[df.index[i], 'market_structure'] == 'Bullish':
            df.at[df.index[i], 'entry'] = df.loc[df.index[i], 'close']
            df.at[df.index[i], 'take_profit'] = df.loc[df.index[i], 'resistance']
            df.at[df.index[i], 'stop_loss'] = df.loc[df.index[i], 'support']
        elif df.loc[df.index[i], 'market_structure'] == 'Bearish':
            df.at[df.index[i], 'entry'] = df.loc[df.index[i], 'close']
            df.at[df.index[i], 'take_profit'] = df.loc[df.index[i], 'support']
            df.at[df.index[i], 'stop_loss'] = df.loc[df.index[i], 'resistance']
        
        risk = abs(df.at[df.index[i], 'entry'] - df.at[df.index[i], 'stop_loss'])
        reward = abs(df.at[df.index[i], 'take_profit'] - df.at[df.index[i], 'entry'])
        
        if reward > 0 and risk > 0:
            risk_to_reward_ratio = reward / risk
            df.at[df.index[i], 'risk_to_reward'] = risk_to_reward_ratio
            
            if risk_to_reward_ratio < MIN_RISK_REWARD_RATIO:
                df.at[df.index[i], 'take_profit'] = df.at[df.index[i], 'entry'] + MIN_RISK_REWARD_RATIO * risk
                
                reward = abs(df.at[df.index[i], 'take_profit'] - df.at[df.index[i], 'entry'])
                risk_to_reward_ratio = reward / risk
                df.at[df.index[i], 'risk_to_reward'] = risk_to_reward_ratio

    latest_signal = df.dropna(subset=['entry']).iloc[-1]
    return {
        'entry': latest_signal['entry'],
        'take_profit': latest_signal['take_profit'],
        'stop_loss': latest_signal['stop_loss'],
        'risk_to_reward': latest_signal['risk_to_reward']
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_signal')
def get_signal():
    try:
        data = get_live_data(SYMBOL, INTERVAL, API_KEY)
        signals = smc_strategy(data)
        return jsonify(signals)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == "__main__":
    app.run(debug=True)
