import pandas as pd
from pythainlp.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC
from sklearn.preprocessing import normalize

chatlog = pd.read_pickle('./data/chatlog.p') 
df = chatlog[['userId', 'message', 'role', '_date']]    
df.drop(df[df.role == "Admin"].index, inplace=True)  
df_11_01 = df[df._date == "2019-11-01"] 
id_list = df_11_01['userId'].unique()
vectorizer = CountVectorizer(tokenizer=word_tokenize)
