import pandas as pd
from datetime import date

# Read data
df_postback = pd.read_csv('./data/postback_response.csv')
print('Reading postback_response data...')

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")

# Utils
def to_dategooglesheet(date):
	return date.strftime('%Y%m%d')

def to_datestr(date):
	return date.strftime('%Y-%m-%d')

def get_date(text):
    date = text[:10]
    return date


# # Create new dataframe to store relevant data
# postback_response = pd.DataFrame(columns=['date', 'postback_payload','no. of messages'])


# Extract date from datetime column
def clean_postback(df_postback, start_date: str=td, end_date: str=td):
    df_postback['date'] = df_postback.datetime.apply(lambda x: get_date(x))
    df_postback = df_postback.loc[df_postback.postback_type=='button'].reset_index()
    return df_postback[(df_postback.date >= start_date) & 
    (df_postback.date <= end_date)]


# Get postback_payload count
def count_postback_payload(df_postback):
    df_payload = df_postback.groupby('postback_payload').count()
    df_payload.sort_values('postback_type', ascending=False, inplace=True)
    df_payload = df_payload[['postback_type']]
    return df_payload.rename(columns={"postback_type": "access_count"}).head(20)

# Main
df_postback_clean = clean_postback(df_postback)
df_postback_count = count_postback_payload(df_postback_clean)
df_postback_count.to_excel('./excel/postback_response_{}.xlsx'.format(td))