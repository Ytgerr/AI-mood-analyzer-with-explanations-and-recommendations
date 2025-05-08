from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import re
from contextlib import asynccontextmanager
from functools import partial
from nltk.corpus import stopwords
import nltk
from scipy.sparse import csr_matrix
from lime.lime_text import LimeTextExplainer
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from scipy.sparse import hstack

nltk.download('stopwords')
stop_words = stopwords.words("english")
    
class Item(BaseModel):
    text: str

def dataPrepare():
    data = pd.read_csv("dataset/train.csv", encoding="latin1")
    test_data = pd.read_csv("dataset/test.csv", encoding="latin1")
    df = pd.concat([data, test_data])
    df.drop(columns=['textID', 'selected_text', 'Population -2020', 'Land Area (Km²)', 'Density (P/Km²)', 'Country'], axis=1, inplace=True)
    df.dropna(inplace=True)
    
    def clean_text(raw_text):
        text = re.sub(re.compile('<.*?>'), '', str(raw_text))
        text = re.sub(r'[^a-zA-Z0-9\s]', '', str(text))
        text = re.sub(r'\s+', ' ', str(text)).strip()
        text = str(text).lower()
        if isinstance(text, str):
            text = re.sub(r'[^\w\s]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
        else:
            text = str(text)
        return text

    df['text'] = df['text'].apply(clean_text)
    df['text'] = df['text'].apply(lambda x: [item for item in x.split() if item not in stop_words]).apply(lambda x:" ".join(x))
    
    def remove_urls(text):
        pattern = re.compile(r'\b(?:http|https|www)\S*')
        return pattern.sub(r'', text)

    df["text"] = df["text"].apply(remove_urls)
    df = df.reset_index(drop=True)
    return df
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    df = dataPrepare()
    y = df['sentiment']
    X = df.drop(['sentiment'], axis=1)
    
    encoder = LabelEncoder()
    y = encoder.fit_transform(y)
    
    cv = CountVectorizer()
    X_text = cv.fit_transform(X["text"])
    
    encoder_time = OneHotEncoder(sparse_output=False)
    new_time = encoder_time.fit_transform(df[['Time of Tweet']])
    
    encoder_age = OneHotEncoder(sparse_output=False)
    new_age = encoder_age.fit_transform(df[['Age of User']])
    
    X_combined = hstack([X_text, new_time, new_age])
    model = LogisticRegression(max_iter=1000, n_jobs=1)
    model.fit(X_combined, y)
    
    app.state.model = model
    app.state.vectorizer = cv
    app.state.time_encoder = encoder_time
    app.state.age_encoder = encoder_age
    
    yield
    
app = FastAPI(lifespan=lifespan)


def map_label(n):
    if n == 0:
        return "Negative"
    elif n == 1:
        return "Neutral"
    elif n == 2:
        return "Positive"
    
def age_to_range(age):
    if 0 <= age <= 20:
        return '0-20'
    elif 21 <= age <= 30:
        return '21-30'
    elif 31 <= age <= 45:
        return '31-45'
    elif 46 <= age <= 60:
        return '46-60'
    elif 61 <= age <= 70:
        return '60-70'
    else:
        return '70-100'

def text_clean(text):
    text = re.sub(re.compile('<.*?>'), '', str(text))
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.lower()
    clean_text = " ".join([word for word in text.split() if word not in stop_words])
    return clean_text

def lime_predict_proba(texts, time_matrix, age_matrix, request: Request):
    features = []
    for t in texts:
        t_clean = text_clean(t)
        cv = request.app.state.vectorizer
        t_vector = cv.transform([t_clean])
        t_feature = hstack([t_vector, time_matrix, age_matrix])
        features.append(t_feature)
    feature_matrix = np.vstack([f.toarray() for f in features])
    feature_matrix = csr_matrix(feature_matrix)
    model = request.app.state.model
    return model.predict_proba(feature_matrix)
    


@app.post("/process/")
def process_text(item: Item, request: Request):
    
    text = text_clean(item.text)
    time = "morning"
    age = 20
    
    cv = request.app.state.vectorizer
    text_vector = cv.transform([text])
    
    encoder_time = request.app.state.time_encoder
    encoder_age = request.app.state.age_encoder
    
    time_df = pd.DataFrame([[time]], columns=["Time of Tweet"])
    time_matrix = encoder_time.transform(time_df)
    
    age_range = age_to_range(age)
    age_df = pd.DataFrame([[age_range]], columns=["Age of User"])
    age_matrix = encoder_age.transform(age_df)
        
    feature = hstack([text_vector, time_matrix, age_matrix]) 

    model = request.app.state.model
    pred = model.predict(feature)

    explainer = LimeTextExplainer(class_names=["negative", "neutral", "positive"])
    
    lime_predict = partial(lime_predict_proba, time_matrix=time_matrix, age_matrix=age_matrix, request=request)
    explanation = explainer.explain_instance(text, lime_predict, num_features=10)
    
    
    top_important_words = explanation.as_list()[:3]
    explanation_words = [
    {"word": word, "score": round(score, 3)}
    for word, score in top_important_words
]
    
    return {
    "label": map_label(pred),
    "explanation": explanation_words
}