# Import necessary libraries
from flask import Flask, request, jsonify,Response
import requests
import os
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime
import news_analysis
import rahul_analysis
import timeseriesprediction
import lstmprediction
import pandas as pd
from flask_cors import CORS


news_sentiment=news_analysis.get_news_report()
# Get today's date
today = datetime.now()
start_date = '2023-01-01'
# Format the date as "YYYY-MM-D"
end_date = today.strftime('%Y-%m-%d')
company_tickers = {
    "microsoft": "MSFT",
    'tata motors':"TATAMOTORS.NS",
    "cisco": "CSCO",
    "intel": "INTC",
    "apple": "AAPL",
    "tcs": "TCS.NS",
    "hcl": "HCLTECH.NS",
    "nike": "NKE",
    "mcdonald's": "MCD",
    "disney": "DIS",
    "walmart": "WMT",
    "american express": "AXP",
    "goldman": "GS",
    "visa": "V",
    "berkshire": "BRK.A (Class A), BRK.B (Class B)",
    "jpmorgan": "JPM",
    "mastercard": "MA",
    "wells fargo": "WFC",
    "citigroup": "C",
    "hsbc": "HSBC",
    "morgan stanley": "MS",
    "amgen": "AMGN",
    "boeing": "BA",
    "coca-cola": "KO",
    "verizon": "VZ",
    "dlf ltd": "DLF",
    "tata power": "TATAPOWER",
    "indian_oil": "IOC",
    "adani": "ADANIGREEN (Adani Green Energy)",
    "tata motors": "TATAMOTORS",
    "sunpharma": "SUNPHARMA.NS",
    "cipla": "CIPLA.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "ntpc": "NTPC.NS",
    "axis": "AXISBANK.NS",
    "hdfc": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "reliance": "RELIANCE.NS",
    "tata steel": "TATASTEEL.NS",
    "power grid": "POWERGRID",
    "sbi": "SBIN.NS",
    "oil and natural gas": "ONGC",
    "sbi life": "SBILIFE",
    "hdfc life": "HDFCLIFE",
    "tata consumer": "TATACONSUM",
    "airtel": "BHARTIARTL.NS",
    "maruti": "MARUTI.NS",
    "coal india": "COALINDIA.NS",
    "hero": "HEROMOTOCO.NS",
    "eicher motors": "EICHERMOT",
    "hindalco": "HINDALCO",
    "infosys": "INFY.NS",
    "itc": "ITC.NS",
}

app = Flask(__name__)

CORS(app, origins=['http://localhost:3000'], allow_headers=['Content-Type', 'Authorization', 'access-control-allow-methods'], allow_methods=['GET', 'POST', 'PUT', 'DELETE'])

fl=open("log.log","a")


@app.route('/', methods=['GET'])
def handle_preflight():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    return response

@app.route('/newsanalysis', methods=['GET'])
def newsAnalysis():
    return jsonify(news_sentiment)

@app.route('/data/current/<company>', methods=['GET'])
def currentInfo(company):
    ticker = company_tickers[company]
    headers = {'user-agent':'Mozilla/5.0 \ (Windows NT 10.0; Win64; x64) \ AppleWebKit/537.36 (KHTML, like Gecko) \ Chrome/84.0.4147.105 Safari/537.36'} 
    url=f'https://finance.yahoo.com/quote/{ticker}/?p={ticker}'
    page = requests.get(url,headers=headers) 
    soup = BeautifulSoup(page.text, 'html.parser') 
    abc=soup.find('div', {'id': 'quote-header-info'}).find_all('fin-streamer')
    x=[abc[0].text,abc[1].text,abc[2].text] 
    response = Response(jsonify({'values': x}), content_type='application/json')
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'

    return jsonify({'values': x})

def getcurrentInfo(company):
    ticker = company_tickers[company]
    headers = {'user-agent':'Mozilla/5.0 \ (Windows NT 10.0; Win64; x64) \ AppleWebKit/537.36 (KHTML, like Gecko) \ Chrome/84.0.4147.105 Safari/537.36'} 
    url=f'https://finance.yahoo.com/quote/{ticker}/?p={ticker}'
    page = requests.get(url,headers=headers) 
    soup = BeautifulSoup(page.text, 'html.parser') 
    abc=soup.find('div', {'id': 'quote-header-info'}).find_all('fin-streamer')
    return [abc[0].text,abc[1].text,abc[2].text]
    
@app.route('/data/predict/<company>', methods=['GET'])
def predict(company):
    
    fl.write("1\n")
    ticker = company_tickers[company]
    fl.write(f"{ticker}\n")
    file_path="./csvfiles/"+ticker+end_date+".csv"
    fl.write(f"{file_path}\n")
    df=None
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            fl.write(f"file_pathexist file opens\n")
            df = pd.read_csv(file_path)   
    else:
        df= yf.download(ticker, start_date, end_date)
        fl.write(f"data downloaded\n")
        df["Date"]=df.index
        df.to_csv(file_path, index=False)
        fl.write(f"file saved\n")
    # dfw=pd.read_csv("my_weights.csv")
    # print(dfw.head())
    weights = [0.06,0.95,0.01]#[float(value) for value in dfw.iloc[1]}
    weights2 = [0.07,0.93,0.01]
    fl.write(f"got weights\n{weights}\n")
    p1=rahul_analysis.getPrediction(df)
    fl.write(f"p1={p1}\n")
    p2=timeseriesprediction.getPrediction(df)
    fl.write(f"p2={p2}\n")
    p3=news_sentiment[company]
    fl.write(f"p3={p3}\n")
    p4=lstmprediction.getPrediction(df)[0]
    fl.write(f"p4={p4}\n")
    result=(p1*weights[0])+(p2*weights[1])+(p3*weights[2]*p2)
    result2=(p1*weights2[0])+(p4*weights2[1])+(p3*weights2[2]*p4)
    fl.write(f"result={result}\n")
    fl2=open("weigpiphtreg.csv","a")
    closep=0
    try:
        last_index_label = df["Close"].index[-1]
        closep=df["Close"].loc[last_index_label]
    except:
        pass
    fl2.write(f"{p1},{p2},{p3},{p4},{closep},{result}\n")
    fl2.close()
    response = Response(jsonify({'pvalue': str(result),'pvaluelstm': str(result2)}), content_type='application/json')
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'

    return jsonify({'pvalue': str(result),'pvaluelstm': str(result2)})

@app.route('/data/<company>', methods=['GET'])
def getdata(company):
    ticker = company_tickers[company]
    file_path="./csvfiles/"+ticker+end_date+".csv"
    df=None
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            fl.write(f"file_pathexist file opens\n")
            df = pd.read_csv(file_path)   
    else:
        
        df= yf.download(ticker, start_date, end_date)
        fl.write(f"data downloaded\n")
        df["Date"]=df.index
        if(len(df)>2):
            df.to_csv(file_path, index=False)
    # lst=getcurrentInfo(company)
    # dc={'current':lst,'table':df.to_dict(orient='records')}
    response = Response(df.to_json(orient='records'), content_type='application/json')
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    return df.to_json(orient='records')

if __name__ == '__main__':
    app.run(debug=True)
    fl.close()
    
