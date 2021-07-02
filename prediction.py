import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
country = "Vietnam"
#country = "India"
#country = "Japan"

df_confirmed = pd.read_csv("https://raw.githubusercontent.com/HungVoCs47/COVID-19-DATA-PREDICTION/main/covid_19_confirmed_cases.csv")
df_confirmed_country = df_confirmed[df_confirmed["Country/Region"] == country]
df_confirmed_country = pd.DataFrame(df_confirmed_country[df_confirmed_country.columns[4:]].sum(),columns=["confirmed"])
df_confirmed_country.index = pd.to_datetime(df_confirmed_country.index,format='%m/%d/%y')

df_confirmed_country.plot(figsize=(10,5),title="COVID confirmed cases")


print("Total days in the dataset", len(df_confirmed_country))
x = len(df_confirmed_country)-30

train=df_confirmed_country.iloc[:x]
test = df_confirmed_country.iloc[x:]
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
scaler.fit(train) 

train_scaled = scaler.transform(train)
test_scaled = scaler.transform(test)


from keras.preprocessing.sequence import TimeseriesGenerator

seq_size = 7  
n_features = 1
train_generator = TimeseriesGenerator(train_scaled, train_scaled, length = seq_size, batch_size=1)
print("Total number of samples in the original training data = ", len(train)) 
print("Total number of samples in the generated data = ", len(train_generator)) 


x,y = train_generator[10]


#Also generate test data
test_generator = TimeseriesGenerator(test_scaled, test_scaled, length=seq_size, batch_size=1)
print("Total number of samples in the original training data = ", len(test)) 
print("Total number of samples in the generated data = ", len(test_generator)) 
x,y = test_generator[0]

from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Activation


model = Sequential()
model.add(LSTM(150, activation='relu', return_sequences=True, input_shape=(seq_size, n_features)))
model.add(LSTM(64, activation='relu'))
model.add(Dense(64))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

model.summary()
print('Train...')

history = model.fit_generator(train_generator, 
                              validation_data=test_generator, 
                              epochs=250, steps_per_epoch=10)



loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()



prediction = [] 

current_batch = train_scaled[-seq_size:] 
current_batch = current_batch.reshape(1, seq_size, n_features)


future = 7 #Days
for i in range(len(test) + future):
    current_pred = model.predict(current_batch)[0]
    prediction.append(current_pred)
    current_batch = np.append(current_batch[:,1:,:],[[current_pred]],axis=1)


rescaled_prediction = scaler.inverse_transform(prediction)

time_series_array = test.index  #Get dates for test data


for k in range(0, future):
    time_series_array = time_series_array.append(time_series_array[-1:] + pd.DateOffset(1))

df_forecast = pd.DataFrame(columns=["actual_confirmed","predicted"], index=time_series_array)

df_forecast.loc[:,"predicted"] = rescaled_prediction[:,0]
df_forecast.loc[:,"actual_confirmed"] = test["confirmed"]


df_forecast.plot(title="Predictions for next 7 days")
