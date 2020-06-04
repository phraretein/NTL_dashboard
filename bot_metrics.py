# Count the number of non-understood instances
import pandas as pd
import time

# number of processed rows
n_processed = 0
# All counted
df_counted_all = pd.DataFrame(columns=["date", "count"])

while True:
    print("Running")
    submit_to_agent = pd.read_pickle('./data/submit_to_agent_grow.p')
    
    # Extract date from datetime string and remove dashes
    df_to_process = submit_to_agent[n_processed:].copy()
    df_to_process['date'] = df_to_process['datetime'].apply(lambda x: x[:10]).apply(lambda x: x.replace('-', ''))
    
    # Count the number of instances by date group
    df_counted = df_to_process.groupby('date')['reason'].apply(lambda x: (x == 'not_understand').sum()).reset_index(name='count')
    df_counted_all = df_counted_all.append(df_counted)
    
    # Update the latest number of processed rows
    n_processed = submit_to_agent.shape[0]

    df_counted_all['count'] = df_counted_all.groupby(['date'])['count'].transform('sum')
    df_counted_all.drop_duplicates()
    
    time.sleep(1)