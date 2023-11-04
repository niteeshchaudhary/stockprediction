import pandas as pd
import numpy as np

import urllib.request
import json
import matplotlib.pyplot as plt

def getPrediction(df):
    # csv_file_path = 'my_data.csv'
    # df = pd.read_csv(csv_file_path)
    myconst=len(df)-1
    rowstotake=myconst

    upcl=df["High"][-rowstotake:].mean()
    dncl=df["Low"][-rowstotake:].mean()

    rs=dncl/upcl

    def f(time_period=0):
        upcl=df["High"][-time_period:].mean()
        dncl=df["Low"][-time_period:].mean()
        rs=dncl/upcl
        return 100-100/(1+rs)

    def g(t,timeperiod):
        smoothening_factor=2/(timeperiod+1)
        if(t==0):
            return ( df["Close"][t] * smoothening_factor )   + df["Close"][t] * ( 1 - smoothening_factor)
            
        return ( df["Close"][t] * smoothening_factor )   +  g (t-1,timeperiod) * ( 1 - smoothening_factor)

    smoothening_factor=2/(rowstotake+1)
    t=rowstotake
    ot=[]
    for i in range(1,t+1):
        ot.append(g(len(df)-1-t+i,t))
        
    return ot[-1]

def getGraph(csv_file_path):
    df = pd.read_csv(csv_file_path)
    myconst=len(df)-1
    rowstotake=myconst

    upcl=df["High"][-rowstotake:].mean()
    dncl=df["Low"][-rowstotake:].mean()

    rs=dncl/upcl

    def f(time_period=0):
        upcl=df["High"][-time_period:].mean()
        dncl=df["Low"][-time_period:].mean()
        rs=dncl/upcl
        return 100-100/(1+rs)

    def g(t,timeperiod):
        smoothening_factor=2/(timeperiod+1)
        if(t==0):
            return ( df["Close"][t] * smoothening_factor )   + df["Close"][t] * ( 1 - smoothening_factor)
            
        return ( df["Close"][t] * smoothening_factor )   +  g (t-1,timeperiod) * ( 1 - smoothening_factor)

    smoothening_factor=2/(rowstotake+1)
    t=rowstotake
    ot=[]
    for i in range(1,t+1):
        ot.append(g(len(df)-1-t+i,t))
        
    plt.figure(figsize=(10,6))
    plt.plot(df["Date"][-rowstotake:], df["Close"][-rowstotake:], color='blue', marker='o')
    plt.plot(df["Date"][-rowstotake:],ot , color='red', marker='x')

    # Add title and labels
    plt.title('Sample Plot')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')

    # Add legend
    plt.legend()

    # Show the plot
    plt.grid(True)
    plt.savefig("rahul.jpg")
    return ot[-1]

if __name__ == '__main__':
    df = getGraph("HCLTECH.NS2023-11-02.csv")