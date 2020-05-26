import pandas as pd

chatlog = pd.read_pickle('./data/chatlog.p') 
df = chatlog[['message', 'role', '_date']]    
df.drop(df[df.role == "Admin"].index, inplace=True)  
df_11_01 = df[df._date == "2019-11-01"] 