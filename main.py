import pandas as pd
import numpy as np
import pickle

from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense

# ==============================
# LOAD DATA
# ==============================
data = pd.read_csv("feeds.csv")

data = data[['field1','field2','field3','field4','field5']]
data.columns = ['temp','humidity','mq7','mq135','dust']

data = data.apply(pd.to_numeric, errors='coerce')
data = data.dropna()

# ==============================
# FEATURES
# ==============================
X = data[['temp','humidity','mq7','mq135','dust']]

# ==============================
# NORMALIZE
# ==============================
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# ==============================
# XGBOOST MODEL (MULTI OUTPUT)
# ==============================
xgb = XGBRegressor()
xgb.fit(X_scaled, X_scaled)

# ==============================
# GRU MODEL (MULTI OUTPUT)
# ==============================
X_gru = np.reshape(X_scaled, (X_scaled.shape[0], 1, X_scaled.shape[1]))

model = Sequential()
model.add(GRU(64, input_shape=(1, X_scaled.shape[1])))
model.add(Dense(5))   # 🔥 5 outputs (all fields)

model.compile(optimizer='adam', loss='mse')
model.fit(X_gru, X_scaled, epochs=10, verbose=1)

# ==============================
# FUTURE 24 STEPS
# ==============================
future = []

last_input = X_scaled[-1].reshape(1,1,5)

for i in range(24):
    gru_out = model.predict(last_input)[0]
    xgb_out = xgb.predict(last_input.reshape(1,-1))[0]

    final = (gru_out + xgb_out) / 2
    future.append(final)

    last_input = final.reshape(1,1,5)

# Convert back to real values
future = scaler.inverse_transform(future)

future_df = pd.DataFrame(future, columns=['temp','humidity','mq7','mq135','dust'])

# AQI calculation
future_df['aqi'] = (0.4*future_df['mq135'] +
                    0.3*future_df['dust'] +
                    0.2*future_df['mq7'] +
                    0.1*future_df['temp'])

future_df.to_csv("future_full_24hrs.csv", index=False)

# Save models
pickle.dump(xgb, open("xgb_model.pkl","wb"))
model.save("gru_model.keras")
pickle.dump(scaler, open("scaler.pkl","wb"))

print("✅ FULL FUTURE PREDICTION READY")