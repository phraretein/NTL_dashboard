import pandas as pd
# import re
# import string
from datetime import date

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")

# Read data
print("Reading submit_to_agent data...")
submit_to_agent = pd.read_csv('./data/submit_to_agent_update.csv') 


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
    submit_to_agent_group = submit_to_agent.groupby(['last_bot_message','message','date_googlesheet']).count()
    submit_to_agent_group.sort_values('reason', ascending=False, inplace=True)
    submit_to_agent_group = submit_to_agent_group[['reason']]
    return submit_to_agent_group.rename(columns={"reason": "occurences"})


# Main
print("Processing data...")
submit_to_agent_clean = clean_submit_to_agent(submit_to_agent)
dropout_group = group_dropout(submit_to_agent_clean)
print("Exporting dropout group to /excel ...")
dropout_group.to_excel('./excel/dropout_loc_{}.xlsx'.format(td), merge_cells=False)
print("Exported dropout group to excel. Data is up to {}.".format(td))
