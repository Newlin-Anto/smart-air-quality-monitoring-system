from flask import Flask, render_template
import pandas as pd
import numpy as np
import requests
import pickle
from tensorflow.keras.models import load_model

app = Flask(__name__)

# Load models
xgb = pickle.load(open("xgb_model.pkl", "rb"))
gru = load_model("gru_model.h5", compile=False)
scaler = pickle.load(open("scaler.pkl", "rb"))

CHANNEL_ID = "3307158"
READ_API_KEY = "MTHPG94RR4IG6B5H"

URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=50"

# =========================
# GET LIVE DATA
# =========================
def get_data():
    data = requests.get(URL).json()
    df = pd.DataFrame(data['feeds'])

    df = df[['field1','field2','field3','field4','field5']]
    df.columns = ['temp','humidity','mq7','mq135','dust']

    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()

    return df

# =========================
# AQI
# =========================
def calculate_aqi(df):
    df['aqi'] = (0.4*df['mq135'] +
                 0.3*df['dust'] +
                 0.2*df['mq7'] +
                 0.1*df['temp'])
    return df

# =========================
# FUTURE PREDICTION
# =========================
def predict_future(df):

    X = df[['temp','humidity','mq7','mq135','dust']]
    X_scaled = scaler.transform(X)

    last_input = X_scaled[-1].reshape(1,1,5)

    future = []

    for i in range(24):
        gru_out = gru.predict(last_input)[0]
        xgb_out = xgb.predict(last_input.reshape(1,-1))[0]

        final = (gru_out + xgb_out) / 2

        # convert to real values
        real = scaler.inverse_transform([final])[0]

        # AQI
        aqi = (0.4*real[3] + 0.3*real[4] + 0.2*real[2] + 0.1*real[0])

        future.append({
            "temp": round(real[0],2),
            "hum": round(real[1],2),
            "mq7": round(real[2],2),
            "mq135": round(real[3],2),
            "dust": round(real[4],2),
            "aqi": round(aqi,2)
        })

        last_input = final.reshape(1,1,5)

    return future
# =========================
# ROUTE
# =========================
@app.route("/")
def home():

    df = get_data()
    df = calculate_aqi(df)

    latest = df.iloc[-1]

    future = predict_future(df)

    return render_template("index.html",
                           temp=latest['temp'],
                           hum=latest['humidity'],
                           mq7=latest['mq7'],
                           mq135=latest['mq135'],
                           dust=latest['dust'],
                           future=future)

if __name__ == "__main__":
    app.run(debug=True)