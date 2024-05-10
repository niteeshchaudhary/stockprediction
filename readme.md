# StockPrediction

- Predict the closing price of stocks with the help of previous data and todays news sentiments.
- The model uses moving average, different stock strategies and news sentiments as factors and predict the closing price.
- Stock and news data is collected using yahoo web scrapping.


# How to run ? 
download model and tokenizer folder from
https://drive.google.com/drive/folders/1PPKOWUygpNf9HfECWR1wLgiKwNWMGFPx?usp=sharing
and place them in backend folder.

goto frontend folder and execute following commands:
npm i --force
to run:
npm start

goto backend folder and execute following commands:
python –m venv env
In linux:
    source env/bin/activate

In Windows:
    env/Scripts/activate

pip install -r requirements.txt
to run:
python server.py
