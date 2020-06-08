import pandas as pd
from datetime import date

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")

# Read data
print("Reading submit_to_agent data...")
submit_to_agent = pd.read_pickle('./data/submit_to_agent.p')

def get_fbr_count(submit_to_agent):
    # number of processed rows
    n_processed = 0
    # All counted
    df_counted_all = pd.DataFrame(columns=['date', 'count'])
    # Extract date from datetime string and remove dashes
    df_to_process = submit_to_agent[n_processed:].copy()
    df_to_process['date'] = df_to_process['datetime'].apply(lambda x: x[:10]).apply(lambda x: x.replace('-', ''))
    # Count the number of instances by date group
    df_counted = df_to_process.groupby('date')['reason'].apply(lambda x: (x == 'not_understand').sum()).reset_index(name='count')
    df_counted_all = df_counted_all.append(df_counted)
    # Update the latest number of processed rows
    n_processed = submit_to_agent.shape[0]
    df_counted_all['count'] = df_counted_all.groupby(['date'])['count'].transform('sum')
    df_counted_all.rename(columns={"count": "no. of not_understand"})
    return df_counted_all.drop_duplicates()

# Main
print("Processing data...")
submit_to_agent_count = get_fbr_count(submit_to_agent)
print('Exporting to /excel ...')
submit_to_agent_count.to_excel('./excel/fbr_not_understand_{}.xlsx'.format(td))
print('Export complete.')