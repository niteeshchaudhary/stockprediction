from bs4 import BeautifulSoup as BS
import requests as req

from transformers import BertForSequenceClassification, BertTokenizer
import spacy
from transformers import AutoModelForSequenceClassification, AutoTokenizer,pipeline
import torch
# Load the model and tokenizer
model = BertForSequenceClassification.from_pretrained("./model")
tokenizer = BertTokenizer.from_pretrained("./tokenizer")

gv_sectors=["technology",
"healthcare",
"financial services",
"consumer discretionary",
"consumer staples",
"energy",
"industrial",
"utilities",
"materials",
"real estate",
"communication services",
"consumer services",
"transportation",
"defense and aerospace",
"healthcare",
"services",
"technology",
"hardware",
"software",
"energy",
"biotechnology",
"consumer electronics"
]
company_names = {'cipla':0,"tata steel":0,"tata motors":0,"sunpharma":0,"adani":0,"indian oil":0,"tata power":0,"dlf ltd":0,"walmart":0,"nike":0,"coca-cola":0,"microsoft":0,"american express":0,"amgen":0,"boeing":0,"cisco":0,"goldman":0,"ibm":0,"intel":0,"mcdonalds":0,"salesforce":0,"verizon":0,"visa":0,"walmart":0,"disney":0,'apple':0,'tcs':0,'hcl':0,'kotak':0,'berkshire':0, 'visa':0,'jpmorgan':0, 'mastercard':0,   'wells fargo':0, 'citigroup':0,  'hsbc':0, 'hdfc':0,  'morgan stanley':0,"infosys":0,"itc":0,"hindalco":0,"eicher motors":0,"hero":0,"coal india":0,"maruti":0,"airtel":0,"tata consumer":0,"sbi life":0,"oil and natural gas":0,"sbi":0,"power grid":0,'ntpc':0,'reliance':0,'bajaj finance':0,'axis':0,'icici':0
}
company_sector_dict = {
    "technology": ["microsoft", "cisco", "intel", "apple", "tcs", "hcl"],
    "consumer discretionary": ["nike", "mcdonald's", "disney", "walmart"],
    "finance": [
        "american express",
        "goldman",
        "visa",
        "berkshire",
        "jpmorgan",
        "mastercard",
        "wells fargo",
        "citigroup",
        "hsbc",
        "morgan stanley",
        "bajaj finance", "axis", "hdfc", "icici"
    ],
    "healthcare": ["amgen"],
    "industrial": ["boeing"],
    "consumer staples": ["coca-cola"],
    "communication": ["verizon","airtel"],
    "IT": ["infosys"],
    "utilities": [],  # No utilities companies were in the provided list
    "real estate": ["dlf ltd"],
    "energy":["tata power","indian oil","adani","ntpc", "reliance", "oil and natural gas", "coal india"],
    "materials":[],
    "consumer services":[],
    "transportation":[],
    "healthcare": [],
    "hardware": [],
    "software": ["american express",
        "goldman",
        "berkshire",
        "jpmorgan",
        "morgan stanley","tcs","hcl"],
    "biotechnology": [],
    "electronics": [],
    "automobiles": ["tata motors", "maruti suzuki", "hero", "eicher motors"],
    "pharmaceuticals": ["sunpharma", "cipla"],
    "insurance": ["SBI Life Insurance Company", "HDFC Life Insurance Company"],
    "metals": ["tata steel", "hindalco"],

}

# Load spaCy NER model
nlp = spacy.load("en_core_web_sm")

# Custom sector dictionary
sector_keywords = {
    "technology": ["tech", "technology", "IT", "information technology"],
    "finance": ["finance", "banking", "financial", "investment","bajaj finance"],
    "healthcare": ["healthcare", "medical", "biotech"],
    "consumer discretionary": ["retail", "consumer discretionary", "automotive"],
    "consumer staples": ["consumer staples", "grocery", "household"],
    "energy": ["energy", "oil", "gas", "renewable energy"],
    "industrial": ["industrial", "manufacturing", "construction"],
    "utilities": ["utilities", "electricity", "water", "gas"],
    "materials": ["materials", "chemicals", "building materials"],
    "real estate": ["real estate", "property", "REIT"],
    "communication services": ["communication", "media", "telecom"],
    "consumer services": ["consumer services", "travel", "leisure"],
    "transportation": ["transportation", "logistics", "shipping"],
    "healthcare": ["healthcare services", "managed care"],
    "hardware": ["technology hardware", "hardware", "electronics"],
    "software": ["software", "IT services", "software development"],
    "biotechnology": ["biotechnology", "biotech", "medical research"],
    "electronics": ["consumer electronics", "electronics", "gadgets"]
}

# Function to analyze sentiment and detect sectors in news
def analyze_news(news_text):
    # Sentiment Analysis
    # result = classifier(news_text)[0]
    # print(result)
    inputs = tokenizer(news_text, return_tensors="pt", padding=True, truncation=True)
    outputs = model(**inputs)
    sentiment_score = outputs.logits[0]
    #sentiment_score=result['score']
    # print(sentiment_score)
    # Apply the threshold to the overall sentiment score
    sentiment = 1 if sentiment_score[0] > 0.1 else -1 if sentiment_score[1] > 0.23 else 0

    # Named Entity Recognition using the custom sector dictionary
    # doc = nlp(news_text)
    # for ent in doc.ents:
    #     if ent.label_ == "ORG":
    #         sectors.append(ent.text)
    
    # # Extract sectors using the custom dictionary
    for sector, keywords in sector_keywords.items():
        for keyword in keywords:
            if keyword.lower() in news_text.lower():
                for i in company_sector_dict[sector]:
                    company_names[i]+=sentiment
                
    for name in company_sector_dict.keys():
        if name.lower() in news_text.lower():
            for i in company_sector_dict[name]:
                company_names[i]+=sentiment
                
    for name in company_names.keys():
        if name.lower() in news_text.lower():
            company_names[name]+=sentiment


def get_news_report():
    links=['https://finance.yahoo.com/topic/yahoo-finance-originals','https://finance.yahoo.com/topic/stock-market-news/','https://finance.yahoo.com/live/politics/','https://finance.yahoo.com/topic/economic-news','https://finance.yahoo.com/topic/morning-brief/']
    for i in links:
        try:
            news=getNews(i)
            for j in news:
                analyze_news(str(j))
        except:
            print("error*"*5)
            pass
        
    return company_names

def getNews(url = "https://finance.yahoo.com/topic/yahoo-finance-originals"):
    webpage = req.get(url)
    trav = BS(webpage.content, "html.parser")
    for element in trav.find_all('u', class_='StretchedBox'):
        element.decompose()
        
    news=[]
    for link in trav.find_all('a'):
        if(str(type(link)) == "<class 'bs4.element.Tag'>" and link.string 
            and len(link.string) > 30):
            news.append(link.string)
    return news

if __name__ == '__main__':
    df = get_news_report()
    print(df)

