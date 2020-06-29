import os
import pytz
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pymongo import MongoClient

CONVERSATION_TIMELIMIT = timedelta(minutes=5)
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

mlab_client = MongoClient(
    "mongodb://heroku_0n2r8pw1:ptuetisq6abh9ec3vhg0idisa8@ds249808-a0.mlab.com:49808,ds249808-a1.mlab.com:49808/heroku_0n2r8pw1?replicaSet=rs-ds249808&retryWrites=false")
mlab = mlab_client["heroku_0n2r8pw1"]


tz = pytz.timezone('Asia/Bangkok')

day_ago = datetime.now(tz) - timedelta(days=1)
day_ago_str = day_ago.strftime('%Y-%m-%d')

# when you need crontab daily period
# MIN_DATE = day_ago_str
# MAX_DATE = day_ago_str
# start_period_str = day_ago.strftime('%Y-%m-%d 00:00:00')
# end_period_str = day_ago.strftime('%Y-%m-%d 23:59:59')

# when you need crontab custom period
MIN_DATE = "2020-05-31"
MAX_DATE = "2020-06-26"
start_period_str = MIN_DATE + " 00:00:00"
end_period_str = MAX_DATE + " 23:59:59"


time_tmp = time.time()
print(start_period_str, end_period_str)

# ---------------------------------------------

chatlog_data = mlab.agentchatlog.aggregate(
    [{"$project": {"userID": 1, "full_name": 1, "messageDetail": 1, "channel": 1}},
     {"$unwind": "$messageDetail"},
     {"$match": {"messageDetail.time": {"$gte": start_period_str,
                                        "$lte": end_period_str}}},
     {"$project": {"userID": 1, "messageDetail": 1, "full_name": 1, "_id": 0}}
     ])

chatlog = pd.DataFrame(list(chatlog_data))
chatlog['userId'] = chatlog['userID']
chatlog['message'] = [d.get('message') for d in chatlog.messageDetail]
chatlog['role'] = [d.get('role') for d in chatlog.messageDetail]
chatlog['time'] = [d.get('time') for d in chatlog.messageDetail]
chatlog['_date'] = chatlog['time'].astype('str').str[0:10]
chatlog['_time'] = chatlog['time'].astype('str').str[11:16]
botlog = chatlog.loc[chatlog.role == 'Admin'].copy()

chatlog = chatlog[['userId', 'full_name', 'message', 'role', 'time', '_date', '_time']]


chatlog.to_csv("../excel/chatlog.csv", index=False)