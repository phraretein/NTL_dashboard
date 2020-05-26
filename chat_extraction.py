import pandas as pd
import re
import json
from multiprocessing import Pool
import datetime

def extract_chat(role='User',file='chatlogs/agentchatlog.json',nPool=5):
#     Input role='User' or 'Admin' to extract text data from json file
    dat = open(file,'r')
    data = dat.readlines()
    data_list = [(i, data[i]) for i in range(len(data))]
#     df = getchatlog(role,data_list[0])
    p = Pool(nPool)
    if role=='All':
        result = p.map(getchatlog_all, data_list)
    elif role=='User':
        result = p.map(getchatlog_user, data_list)
    elif role=='Admin':
        result = p.map(getchatlog_bot, data_list)
    return pd.concat(result)

def getchatlog_all(list_element):
    index = list_element[0]
    data = json.loads(list_element[1])
#     print(data)
    
    userID = data['userID']
    full_name = data['full_name']
    msgList = data['messageDetail']
    mList = []
    for m in msgList:
#         if m['role']=='User':
        mList.append(m)
    dat = pd.DataFrame(data=mList,columns=['message','time','role'])
    dat['userId'] = userID
    dat['full_name'] = full_name
    dat['_date'] = dat['time'].astype('str').str[0:10]
    dat['_time'] = dat['time'].astype('str').str[11:16]
    dat = dat[['userId','full_name','message','role','_date','_time']]
    return dat

def getchatlog_user(list_element):
    index = list_element[0]
    data = json.loads(list_element[1])
#     print(data)
    
    userID = data['userID']
    full_name = data['full_name']
    msgList = data['messageDetail']
    mList = []
    for m in msgList:
        if m['role']=='User':
            mList.append(m)
    dat = pd.DataFrame(data=mList,columns=['message','time'])
    dat['userId'] = userID
    dat['full_name'] = full_name
    dat['_date'] = dat['time'].astype('str').str[0:10]
    dat['_time'] = dat['time'].astype('str').str[11:16]
    dat = dat[['userId','full_name','message','_date','_time']]
    return dat

def getchatlog_bot(list_element):
    index = list_element[0]
    data = json.loads(list_element[1])
#     print(data)
    
    userID = data['userID']
    full_name = data['full_name']
    msgList = data['messageDetail']
    mList = []
    for m in msgList:
        if m['role']=='Admin':
            mList.append(m)
    dat = pd.DataFrame(data=mList,columns=['message','time'])
    dat['userId'] = userID
    dat['full_name'] = full_name
    dat['_date'] = dat['time'].astype('str').str[0:10]
    dat['_time'] = dat['time'].astype('str').str[11:16]
    dat = dat[['userId','full_name','message','_date','_time']]
    return dat

def combine_text(data,id_col,text_col):
    user_list = list(set(data[id_col]))
    no_of_msg = 0
    new_df = []
    for user in user_list:
        dat = data[data[id_col]==user]
        no_of_msg = len(dat)
        message = dat[text_col].to_list()
        new_df.append([user,no_of_msg,message])
    new_df = pd.DataFrame(data=new_df,columns=['userId','no_of_msg','message'])
    return new_df

def getlastmessage(dat):
    user_list = list(set(dat.userId))
    res = []
    for user in user_list:
        tmp = dat[dat.userId==user]
        res.append([user,tmp.iloc[-1].message])
    return pd.DataFrame(data=res,columns=['userId','message'])

def extract_customer(file='customer.json',nPool = 5):
    dat = open(file,'r')
    data = dat.readlines()
    data_list = [(i, data[i]) for i in range(len(data))]
    p = Pool(nPool)
    result = p.map(getcustdata, data_list)
    return pd.DataFrame(data=result, columns=['custID','brand','model','year','name','number','ins_type_1','ins_type_2'])

def getcustdata(list_element):
    # Extract car information
    index = list_element[0]
    data = json.loads(list_element[1])
    custID = data['customer_id']

    try:
        brand = data['brand']
    except:
        brand = ''

    try:
        model = data['categorybrand']
    except:
        model = ''

    try:
        year = data['year']
    except:
        year = ''

    try:
        name = data['name']
    except:
        name = ''

    try:
        number = data['number']
    except:
        number = ''

    try:
        ins_type_1 = data['insurance']
    except:
        ins_type_1 = ''

    try:
        ins_type_2 = data['insurance1']
    except:
        ins_type_2 = ''

    return [custID,brand,model,year,name,number,ins_type_1,ins_type_2]

def filter_data(df, from_mth=11,from_yr=2019,to_mth=2,to_yr=2020):
  #extract date,year,hr details for plotting
  df['hr'] = df._time.str.slice(0,-3,1).astype(int)
  df['yr'] = df._date.str.slice(0,4,1).astype(int)
  df['mth'] = df._date.str.slice(5,7,1).astype(int)
  df['day'] = df._date.str.slice(8,10,1).astype(int)
  df['_date'] = pd.to_datetime(dict(year=df.yr,month=df.mth,day=df.day)).astype('datetime64[ns]') 

  # filter only data within the given period
#   df = df[((df.mth>=11)&(df.yr==))|(df.yr==2020)]

  current_yr = datetime.now().year

#   from_yr = 2019
  if from_year < current_yr:
      df = df[((df.mth>=from_mth)&(df.yr==from_yr))&((df.mth<=to_mth)&(df.yr==to_yr))]

  # remove user == 'facebook' (program bug)
  df = df[df.userId!='facebook']

  # assign weekday
  df['weekday'] = df['_date'].apply(lambda x: x.strftime('%A'))

  return df