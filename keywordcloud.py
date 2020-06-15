import pandas as pd
import numpy as np
import re
import string
import matplotlib.pyplot as plt
from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from datetime import date
from dateutil.relativedelta import relativedelta
from wordcloud import WordCloud, STOPWORDS

# Read chatlog data
print("Reading chatlog data...")
chatlog = pd.read_pickle('./data/chatlog.p')

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")
one_month = today + relativedelta(months=-1)
td_minus_one_month = one_month.strftime("%Y-%m-%d")


# Clean the chatlog to have only user conversation on specific date (monthly)
def clean_chatlog(chatlog, start_date:str=td_minus_one_month, end_date:str=td):
    df = chatlog[['userId', 'message', 'role', '_date']] 
    df = df.loc[df.role=='User']
    return df[(df._date >= start_date) & (df._date <= end_date)]


# Utils
def get_th_tokens(text):
    text = text.replace('\n', ' ')
    text = text.replace(',', ' ')
    tokens = word_tokenize(text, engine="newmm", keep_whitespace=False)
    return tokens


# Clean undesired text
def clean_text_1(text):
    '''Make text lowercase, remove text in square brackets,
    remove punctuation and remove words containing numbers.'''
    text = text.lower()
    text = re.sub('[.?]', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\n', '', text)
    text = re.sub('[0-9]{1,10}', '', text)
    text = re.sub('นะ|น่ะ|น่า|น้า','',text)
    text = re.sub('คะ|ค่ะ|ค่า|คระ|คร่ะ|คร๊|ค๊','',text)
    text = re.sub('ครับ|คับ|คั้บ|ค้าบ|คร้าบ|คาฟ|ค้าฟ|ฮะ|ฮับ|ฮ้าฟ','',text)
    text = re.sub('จ้า|จ้ะ|จ๊ะ','',text)
    text = re.sub('หน่อย|น่อย','',text)
    text = re.sub('สวัสดี|หวัดดี','',text)
    text = re.sub('ของ','',text)
    # ลบ text ที่อยู่ในวงเล็บ <> ทั้งหมด
    text = re.sub(r'<.?>','', text)
    # ลบ hashtag
    text = re.sub(r'#','',text)
    # ลบ separator เช่น \n \t
    text = ' '.join(text.split())
    text = re.sub('สนใจ','',text)
    text = re.sub('อยากทราบว่า|อยากทราบ','',text)
    text = re.sub('รบกวนสอบถาม|ขอสอบถาม|สอบถาม','',text)
    text = re.sub('ปี','',text)
    text = re.sub('ขอบคุณ','',text)
    text = re.sub('ขอโทษ|ขอโทด','',text)
    text = re.sub('ขอ','',text)
    text = re.sub('ชั้น','',text)
    text = re.sub('เท่าไร|เท่าไหร่|เท่าหรั่ย|เท่าใด|เท่ารัย','',text)
    return text


# Remove stopwords from text
def filter_words(text):
    text = text.replace('\n', ' ')
    text = text.replace(',', ' ')
    stop_words = set(thai_stopwords())
    tokens = word_tokenize(text, engine="newmm", keep_whitespace=False)
    filtered_text = []
    for w in tokens:
        if w not in stop_words:
            filtered_text.append(w)
    return filtered_text


# Remove digits from messages
def remove_digits(text):
    output = re.sub(r'\d+', '', text)
    return output


# Remove emojis from messages
def remove_emoji(string):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               u"\u200B"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


# Combine all the text cleaning functions
def clean_text_full(df):
    df = df.groupby(['userId'])['message'].apply(','.join).reset_index()
    df['message'] = df['message'].apply(lambda x: clean_text_1(x))
    df['message'] = df['message'].apply(lambda x: remove_emoji(x))
    df['message'] = df['message'].apply(lambda x: remove_digits(x))
    df['message'] = df['message'].apply(lambda x: filter_words(x))
    df['message'] = df['message'].apply(lambda x: " ".join(x))
    return df


# Find top 20 keywords that has the highest TF-IDF average score
def top_20_keywords(df):
    vectorizer = TfidfVectorizer(tokenizer=get_th_tokens, token_pattern=None, ngram_range=(3,3), min_df=2) 
    vectorizer.fit(df['message']) 
    feat_clean = vectorizer.transform(df['message']) 
    feat_clean_array = feat_clean.toarray() 
    avg_tfidf = feat_clean_array.sum(axis=0) / len(df['userId']) 
    result_clean = pd.DataFrame() 
    result_clean['word'] = vectorizer.get_feature_names() 
    result_clean['avg_tfidf'] = avg_tfidf 
    result_clean['word'] = result_clean['word'].apply(lambda x: x.replace(" ", ""))
    return result_clean.sort_values('avg_tfidf', ascending=False).head(20) 


# Generate word list to for WordCloud process
def gen_text_for_wordcloud(df):
    words = df['word']
    words_to_array = words.tolist()
    return (" ".join(words_to_array))


# Generate WordCloud
def gen_word_cloud(text):
    path = './font/THSarabunNew.ttf'
    wordcloud = WordCloud(font_path=path, width = 800, height = 800, 
                background_color ='white', 
                min_font_size = 10, colormap='coolwarm',regexp = r"[ก-๙a-zA-Z']+", random_state=1).generate(text) 
    # Plot the WordCloud image                        
    plt.figure(figsize = (8, 8), facecolor = None) 
    plt.imshow(wordcloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 


    plt.savefig('./WordCloud/keyword_{}.png'.format(td))


# Main
print("Processing data...")
chatlog_clean = clean_chatlog(chatlog)
chatlog_text_clean = clean_text_full(chatlog_clean)
top_keywords = top_20_keywords(chatlog_text_clean)

print("Exporting top keywords to /excel ...")
top_keywords.to_excel('./excel/topwords_freq_{}.xlsx'.format(td))
print("Exported top keywords to excel. Data is up to {}.".format(td))

print("Generating Wordcloud...")
text_for_wordcloud = gen_text_for_wordcloud(top_keywords)
gen_word_cloud(text_for_wordcloud)
print("Successfully export wordcloud to /WordCloud.")
