import pandas as pd
# import re
# import string
from datetime import date
import pymongo
from pymongo import MongoClient

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")


# Connect to database
def get_data_from_db():
    murl = "mongodb://heroku_0n2r8pw1:ptuetisq6abh9ec3vhg0idisa8@ds249808-a0.mlab.com:49808,ds249808-a1.mlab.com:49808/heroku_0n2r8pw1?replicaSet=rs-ds249808"
    client = MongoClient(murl)
    dbname = 'heroku_0n2r8pw1'
    cl = client[dbname]
    submit_to_agent = cl.submit_to_agent

    submit_to_agent = pd.DataFrame(list(submit_to_agent.find({})))
    return submit_to_agent


# Read data
print("Reading submit_to_agent data...")
submit_to_agent = get_data_from_db()


# Utils
def get_date(text):
    date = text[:10]
    return date


# Clean data to match selection
def clean_submit_to_agent(submit_to_agent, start_date: str=td, end_date: str=td):
    submit_to_agent['date'] = submit_to_agent.datetime.apply(lambda x: get_date(x))
    submit_to_agent['date_googlesheet'] = submit_to_agent['date'].apply(lambda x: x.replace('-', ''))
    submit_to_agent = submit_to_agent[submit_to_agent.reason.isin(['not_understand', 'not_response'])]
    return submit_to_agent[(submit_to_agent.date >= start_date) & (submit_to_agent.date <= end_date)]


# Group dropout by last_bot_message, message, and date
def group_dropout(submit_to_agent):
    submit_to_agent_group = submit_to_agent.groupby(['date_googlesheet', 'last_bot_message', 'message']).count()
    submit_to_agent_group.sort_values('reason', ascending=False, inplace=True)
    submit_to_agent_group = submit_to_agent_group[['reason']]
    return submit_to_agent_group.rename(columns={"reason": "occurences", "date_googlesheet": "date"})


# Main
print("Processing data...")
submit_to_agent_clean = clean_submit_to_agent(submit_to_agent, '2020-03-20')
dropout_group = group_dropout(submit_to_agent_clean)
print("Exporting dropout group to /excel ...")
dropout_group.to_excel('../excel/dropout_loc_{}.xlsx'.format(td), merge_cells=False)
print("Exported dropout group to excel. Data is up to {}.".format(td))
