import pandas as pd
import numpy as np
import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import re
import json
import imp
import calendar
import time
import pymongo
from pymongo import MongoClient
import chat_extraction as ce

# Constants
MIN_DATE = '2019-11-01'
MAX_DATE = '9999-12-31'
CONVERSATION_TIMELIMIT = datetime.timedelta(minutes=5)
DISTANCE_VALUE = 0.6

# Initialize
chatlog = pd.DataFrame()
nlp_dashboard = pd.DataFrame()
submit_to_agent = pd.DataFrame()




# MERGE DATABASE
# ************************************************************
def update_chatlog(chatlog):
	last_date = to_datetime(chatlog._date.max())
	yesterday = to_datetime(to_datestr(datetime.datetime.today())) - timedelta(days=1)
	if last_date < yesterday:
		date_to_query = last_date + timedelta(days=1)
		# client = MongoClient("mongodb+srv://ntlstat:4RBpZqrlUpgKuStd@cluster0-qvbke.mongodb.net/ntlstat")
		# cl = client["ntlstat"]
		murl = "mongodb://heroku_0n2r8pw1:ptuetisq6abh9ec3vhg0idisa8@ds249808-a0.mlab.com:49808,ds249808-a1.mlab.com:49808/heroku_0n2r8pw1?replicaSet=rs-ds249808"
		client = MongoClient(murl)
		dbname = 'heroku_0n2r8pw1'
		cl = client[dbname]
		agentchatlog = pd.DataFrame(list(cl.agentchatlog.find({"messageDetail.time":{"$gte": to_datestr(date_to_query)}})))
		chatlog_to_append = pd.DataFrame(columns=['userId','full_name','message','role','_date','_time'])
		for index, dat in agentchatlog.iterrows():
			chatlog_to_append = chatlog_to_append.append(get_chatlog(dat),ignore_index = True,sort=False)
		chatlog_to_append = chatlog_to_append.log[chatlog_to_append._date<=yesterday] 
		chatlog = chatlog.append(chatlog_to_append, ignore_index=True, sort=False)
	return chatlog

def get_chatlog(data):
	userID = data['userID']
	full_name = data['full_name']
	msgList = data['messageDetail']
	mList = []
	for m in msgList:
		mList.append(m)
	dat = pd.DataFrame(data=mList,columns=['message','time','role'])
	dat['userId'] = userID
	dat['full_name'] = full_name
	dat['_date'] = dat['time'].astype('str').str[0:10]
	dat['_time'] = dat['time'].astype('str').str[11:16]
	return dat[['userId','full_name','message','role','_date','_time']]

# EXTRACTION
# ************************************************************

def extract_user_metrics(startdate,enddate):
	print('Start Extracting User Metrics...')
	result = pd.DataFrame(columns = ['Date','Metric','Count'])
	for date in daterange(startdate,enddate):
		printdate = to_dategooglesheet(date)
		date = to_datestr(date)
		usercount = get_usercount(date)
		activeusercount = get_activeusercount(date)
		engagedusercount = get_engagedusercount(date)
		newusercount = get_newusercount(date)
		result = result.append(pd.Series([printdate,'user',usercount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'active_user',activeusercount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'engaged_user',engagedusercount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'new_user',newusercount],index=['Date','Metric','Count']),ignore_index=True)
		print('Extraction In Progress: %s complete'%date)
	print('====================================Extraction Complete====================================')
	return result

def extract_msg_metrics(startdate,enddate):
	print('Start Extracting Message Metrics...')
	result = pd.DataFrame(columns = ['Date','Metric','Count'])
	for date in daterange(startdate,enddate):
		printdate = to_dategooglesheet(date)
		date = to_datestr(date)
		msgcount = get_msgcount(date,msg_type='total')
		inmsgcount = get_msgcount(date,msg_type='user')
		missmsgcount = get_msgcount(date,msg_type='miss')
		convercount = get_convercount(date)
		newconvercount = get_newconvercount(date)
		result = result.append(pd.Series([printdate,'msg',msgcount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'in_msg',inmsgcount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'miss_msg',missmsgcount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'conver',convercount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'new_conver',newconvercount],index=['Date','Metric','Count']),ignore_index=True)
		print('Extraction In Progress: %s complete'%date)
	print('====================================Extraction Complete====================================')
	return result

def extract_bot_metrics(startdate,enddate):
	print('Start Extracting Bot Metrics...')
	result = pd.DataFrame(columns = ['Date','Metric','Count'])
	for date in daterange(startdate,enddate):
		printdate = to_dategooglesheet(date)
		date = to_datestr(date)
		ret30d, ret90d, ret6m, ret1y = get_retentioncount(date)
		# insleadcount = get_insleadcount(date)
		# converint_max, converint_median, converint_min = get_converintcount(date)
		result = result.append(pd.Series([printdate,'ret30d',ret30d],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'ret90d',ret90d],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'ret6m',ret6m],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'ret1y',ret1y],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'ins_lead',insleadcount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'converint_max',converint_max],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'converint_median',converint_median],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'converint_min',converint_min],index=['Date','Metric','Count']),ignore_index=True)
		print('Extraction In Progress: %s complete'%date)
	print('====================================Extraction Complete====================================')
	return result


# ===========================USER METRICS================================================
# Total users
def get_user(date):
	userlist = chatlog.loc[chatlog.date==date].userId.tolist()
	return list(set(userlist))

def get_user_range(startdate,enddate):
	userlist = []
	for date in daterange(startdate,enddate):
		date = to_datestr(date)
		userlist.extend(get_user(date))
	return list(set(userlist))

def get_usercount(date):
	usercount = len(get_user(date))
	return usercount

# Active Users
def get_activeuser(date):
	interval = 0
	activeuser = []
	currentuser = ''
	currenttime = '0:00'
	active = False
	chatlog_conv = chatlog.loc[chatlog._date==date].sort_values(by=['userId','_time'])
	for index, row in chatlog_conv.iterrows():
		interval = abs(timeinterval(currenttime,row._time))
		
		if row.userId != currentuser:
			if active == True:
				activeuser.append(currentuser)
			currentuser = row.userId
			active = True
		elif (row.role=='User') & (interval > CONVERSATION_TIMELIMIT):
			active = False

		currenttime = row._time

	return list(set(activeuser))

def get_activeusercount(date):
	activeusercount = len(get_activeuser(date))
	return activeusercount

# Engaged Users
def get_engageduser(date):
	userlist = chatlog.loc[chatlog.date==date].userId.tolist()
	return list(set(userlist))

def get_engagedusercount(date):
	engagedusercount = len(get_engageduser(date))
	return engagedusercount

def get_engageduser_range(startdate,enddate):
	userlist = []
	for date in daterange(startdate,enddate):
		date = date.strftime('%Y-%m-%d')
		userlist.extend(get_user(date))
	return list(set(userlist))

# New Users
def get_newuser(date):
	user = get_user(date)

	date = datetime.datetime.strptime(date,'%Y-%m-%d')
	year = date.year
	month = date.month
	
	if month == 1:
		year_prev = year - 1
		month_prev = 12
	else: 
		year_prev = year
		month_prev = month - 1

	startdate = datetime.datetime(year_prev,month_prev,1).strftime('%Y-%m-%d')
	enddate = datetime.datetime(year_prev,month_prev,calendar.monthrange(year_prev, month_prev)[1]).strftime('%Y-%m-%d')
	user_prev = get_user_range(startdate,enddate)

	newuser = list(set(user) - set(user_prev))

	return newuser

def get_newusercount(date):
	newusercount = len(get_newuser(date))
	return newusercount


# ===========================MESSAGE METRICS================================================
# Total messages
# User messages / In-messages (messages users interact with bot)
# Bot messages 
# Miss messages (messages that bot can't process)
def get_msgcount(date,msg_type='total'):
	if msg_type == 'total':
			msg_count = chatlog.loc[chatlog.date==date].message.count()
	elif msg_type == 'bot':
			msg_count = chatlog.loc[(chatlog.date==date)&(chatlog.role=='Admin')].message.count()
	elif msg_type == 'user':
			msg_count = chatlog.loc[(chatlog.date==date)&(chatlog.role=='User')].message.count()
	elif msg_type == 'miss':
			msg_count = get_missmsgcount(date)
	else:
			msg_count = 0
	return msg_count

# drop_out_message
def get_dropoutmsg(date):

    mask_date = submit_to_agent._date == date
    mask_reason = submit_to_agent.reason == 'not_response'

    message = submit_to_agent[mask_date & mask_reason].values.tolist()

    return message

# miss_msg
def get_missmsg(date):

    nlp_dashboard['distance'] = pd.to_numeric(nlp_dashboard['distance'])

    mask_distance = nlp_dashboard.distance >= 0.6
    mask_date = nlp_dashboard._date == date

    return nlp_dashboard.loc[ mask_date & mask_distance ].values.tolist()

def get_missmsgcount(date):
    missmsgcount = len(get_missmsg(date))
    dropout = len(get_dropoutmsg(date))
    return missmsgcount + dropout

# Total conversation (# of conversations completed end-to-end by bot within a day -- engaged users)
def get_conver(date):
	interval = 0
	converpos = 0
	converlist = []
	currentuser = ''
	currenttime = '0:00'
	chatlog_conv = chatlog.loc[chatlog._date==date].sort_values(by=['userId','_time'])
	for index, row in chatlog_conv.iterrows():
		interval = abs(timeinterval(currenttime,row._time))
		if (row.userId != currentuser) | ((row.role=='User')&(interval > CONVERSATION_TIMELIMIT)):
			# print(row.userId,interval,converpos)
			currentuser = row.userId
			converpos += 1
		
		currenttime = row._time
		converlist.append(converpos)
	
	chatlog_conv['conv'] = converlist

	return chatlog_conv

def get_convercount(date):
	chatlog_conv = get_conver(date)
	convercount = chatlog_conv.conv.max()
	return convercount

# New conversation (# of new conversations that are not trained but initiated by users)
def get_newconvercount(date):
    newconver = len(get_missmsg(date))
    return newconver

# ===========================BOT METRICS================================================
def get_retentioncount(date):
	date30d = convertdate(date,-30)
	date90d = convertdate(date,-90)
	date6m = to_datestr(datetime.datetime.strptime(date,'%Y-%m-%d') + relativedelta(months=-6))
	date1y = to_datestr(datetime.datetime.strptime(date,'%Y-%m-%d') + relativedelta(years=-1))

	usertoday = get_user(date)
	user30d = get_user_range(date30d,convertdate(date,-1))
	user90d = get_user_range(date90d,convertdate(date,-1))
	user6m = get_user_range(date6m,convertdate(date,-1))
	user1y = get_user_range(date1y,convertdate(date,-1))

	retention30d = list(np.intersect1d(usertoday,user30d))
	retention90d = list(np.intersect1d(usertoday,user90d))
	retention6m = list(np.intersect1d(usertoday,user6m))
	retention1y = list(np.intersect1d(usertoday,user1y))

	return len(retention30d), len(retention90d), len(retention6m), len(retention1y)


# ===========================OTHER METRICS================================================
# Keyword count (by message)
def get_keywordcount(date, keywordlist, by='message'):
	keywordcount = 0
	if type(keywordlist) != list:
		print("input keywords as a list of strings")
		return None

	dat = chatlog.loc[chatlog.date==date]
	dat.loc[:,'key'] = 0
	for keyword in keywordlist:
		dat.loc[:,'key_temp']=0
		if keyword != "":
			print("keyword:", keyword)

			dat.loc[:,'key_temp'] = dat.message.str.contains(keyword).fillna(0).astype(int)
			dat.loc[:,'key'] = dat[['key','key_temp']].max(axis=1)

	if by == 'message':
		keywordcount = dat.loc[dat.key==1].message.count()
	elif by == 'user':
		keywordcount = dat.loc[dat.key==1].userId.unique.count()
	else:
		keywordcount = 0

	return keywordcount

# Keyword count (by user)

# CALCULATION
# ************************************************************

# Active users

# Engaged users

# New users
def get_userlist_new(startdate,enddate):
	users = userlist(startdate,enddate)
	existing = userlist(MIN_DATE,startdate-1)
	new = list(set(users) - set(users))

	return new

# Retention Rate (% of users that return to use bot)
# Goal Completion Rate (# of leads, No. of Engaged users)
# Goal completion time/messages/taps (Minimizing the effort to complete a goal can improve user experience.) "อยากได้ step ว่าคนเลิกคุยกับ bot ตอนถามคำถามอะไร จะได้นำไปดีไซน์ใหม่"
# Fallback Rate (FBR) (% of chatbot failures happened)


# UTILITIES
def to_datetime(datestr):
	return datetime.datetime.strptime(datestr,'%Y-%m-%d')

def to_datestr(date):
	return date.strftime('%Y-%m-%d')

def to_dategooglesheet(date):
	return date.strftime('%Y%m%d')

def convertdate(date,delta):
	date = datetime.datetime.strptime(date,'%Y-%m-%d')
	date += timedelta(delta)
	return date.strftime('%Y-%m-%d')
	

def daterange(startdate, enddate):
	startdate = datetime.datetime.strptime(startdate,'%Y-%m-%d')
	enddate = datetime.datetime.strptime(enddate,'%Y-%m-%d')
	for n in range(int ((enddate - startdate).days)+1):
		yield startdate + timedelta(n)

def timeinterval(starttime,endtime):
	h1, m1 = starttime.split(':')
	h2, m2 = endtime.split(':')
	interval = datetime.timedelta(hours=(int(h2)-int(h1)), minutes=(int(m2)-int(m1)))

	# 5 mins = datetime.timedelta(0, 300)
	return interval


# In messages (messages users interact with bot)
# Miss messages (messages that bot can't process)
# Total conversation (# of conversations completed end-to-end by bot within a day -- engaged users)
# New conversation (# of new conversations that are not trained but initiated by users)


# Retention Rate (% of users that return to use bot)
# Goal Completion Rate (# of leads, No. of Engaged users)
# Goal completion time/messages/taps (Minimizing the effort to complete a goal can improve user experience.) "อยากได้ step ว่าคนเลิกคุยกับ bot ตอนถามคำถามอะไร จะได้นำไปดีไซน์ใหม่"
# Fallback Rate (FBR) (% of chatbot failures happened)
# User-satisfaction (Did the bot perform well? Y/N)
# Virality (bot that can motivate user to include others in the conversation can achieve viral growth)



# Total Messages
# Pass
# Drop Out
# Sent to Agent


# No. of users entering each step
# คลิกเริ่มเข้าสู่ flow เก็บลีด
# ยี่ห้อรถ
# รุ่นรถ
# ปีรถ
# เลือกชั้นประกัน 1
# เลือกชั้นประกัน 2
# ชื่อ
# เบอร์โทร
# คลิกจุด consent
# No of users dropping out in each step
# คลิกเริ่มเข้าสู่ flow เก็บลีด
# ยี่ห้อรถ
# รุ่นรถ
# ปีรถ
# เลือกชั้นประกัน 1
# เลือกชั้นประกัน 2
# ชื่อ
# เบอร์โทร
# คลิกจุด consent
# No. of users consent / not consent PDPA


# No. of times user asks about each specific intent (42 Intents)
# Ins Auto จำนวน  5 intent
# Loan Mจำนวน  5 intent
# Loan C จำนวน  5 intent
# Loan T จำนวน  5 intent
# HR Job Application 
# Branch Location 
# Payment Inquiry 
# Financial 3 flow


# แสดงจำนวน user ที่ประเมินความพึงพอใจของ bot แยกเป็นพอใจและไม่พอใจ


# เก็บใน data mart รายวัน รายเดือน รายปี

# เขียน api

# ทำ cron job

print('read chatlog ..')
chatlog = pd.read_pickle('./data/chatlog.p')
# print('update chatlog ..')
# chatlog = update_chatlog(chatlog)
print('read nlp_dashboard ..')
nlp_dashboard = pd.read_pickle('./data/nlp_dashboard.p')

print('read submit_to_agent ..')
submit_to_agent = pd.read_pickle('./data/submit_to_agent.p')

print('format date ..')

chatlog['date'] = chatlog._date

nlp_dashboard['_date'] = pd.to_datetime(nlp_dashboard['date'])
nlp_dashboard['_date'] = nlp_dashboard['_date'].dt.strftime('%Y-%m-%d')

submit_to_agent['_date'] = pd.to_datetime(submit_to_agent['datetime'])
submit_to_agent['_date'] = submit_to_agent['_date'].dt.strftime('%Y-%m-%d')