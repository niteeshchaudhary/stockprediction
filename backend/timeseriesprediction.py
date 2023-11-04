import numpy as np 
import numpy as npr 
import pandas as pd 
import os
from subprocess import check_output
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
from pandas.plotting import lag_plot
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
import datetime

def smape_kun(y_true, y_pred):
    return np.mean((np.abs(y_pred - y_true) * 200/ (np.abs(y_pred) + np.abs(y_true))))

def getPrediction(df):
    # df = pd.read_csv("my_data.csv").fillna(0)
    datalen=len(df)
    train_data, test_data = df[max(datalen-100,0):-1], df[max(datalen-100,0):]
    train_ar = train_data['Close'].values
    test_ar = test_data['Close'].values
    test_ar=npr.append(test_ar, test_ar[-1])
    history = [x for x in train_ar]
    predictions = list()
    for t in range(len(test_ar)):
        model = ARIMA(history, order=(5,1,0))
        model_fit = model.fit()
        output = model_fit.forecast()
        yhat = output[0]
        predictions.append(yhat)
        obs = test_ar[t]
        history.append(obs)
        #print('predicted=%f, expected=%f' % (yhat, obs))
    error = mean_squared_error(test_ar, predictions)
    print('Testing Mean Squared Error: %.3f' % error)
    error2 = smape_kun(test_ar, predictions)
    print('Symmetric mean absolute percentage error: %.3f' % error2)

    
    return predictions[-1]

def getgraph(df):
    # df = pd.read_csv("my_data.csv").fillna(0)
    datalen=len(df)
    train_data, test_data = df[max(datalen-100,0):-1], df[max(datalen-100,0):]
    train_ar = train_data['Open'].values
    test_ar = test_data['Open'].values
    history = [x for x in train_ar]
    predictions = list()
    for t in range(len(test_ar)):
        model = ARIMA(history, order=(5,1,0))
        model_fit = model.fit()
        output = model_fit.forecast()
        yhat = output[0]
        predictions.append(yhat)
        obs = test_ar[t]
        history.append(obs)
        #print('predicted=%f, expected=%f' % (yhat, obs))
    error = mean_squared_error(test_ar, predictions)
    print('Testing Mean Squared Error: %.3f' % error)
    error2 = smape_kun(test_ar, predictions)
    print('Symmetric mean absolute percentage error: %.3f' % error2)

    plt.figure(figsize=(12,7))

    plt.plot(test_data.index[-20:], test_data['Open'][-20:], color='red', label='Actual Price')
    plt.title('Prices Prediction')

    plt.plot(df['Open'][-20:-1],  color='blue', label='Training Data')

    plt.plot(test_data.index[-9:], predictions[-9:], color='green', marker='o', linestyle='dashed', 
            label='Predicted Price')
    plt.xlabel('Dates')
    plt.ylabel('Prices')
    plt.xticks(np.arange(max(datalen-20,0),datalen, 2), df['Date'][max(datalen-20,0):datalen:2])
    plt.legend()
    plt.savefig("tseries.jpg")
    return predictions[-1]

if __name__ == '__main__':
    df = pd.read_csv("HCLTECH.NS2023-11-02.csv").fillna(0)
    getgraph(df)
    pass