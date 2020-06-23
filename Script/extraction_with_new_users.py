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
CONFIDENCE_VALUE = 0.6

# Initialize
chatlog = pd.DataFrame()
nlp_dashboard = pd.DataFrame()
submit_to_agent = pd.DataFrame()
# goal = pd.read_excel('./mapping/goal.xlsx')
# goal.Keywords = goal.Keywords.apply(lambda x: x.split(','))
# inq_flow = pd.read_excel('./mapping/inquiry_report.xlsx',sheet_name='Flow')
# inq_flow.messages = inq_flow.messages.fillna('').apply(lambda x: x.split(','))
# inq_nonflow = pd.read_excel('./mapping/inquiry_report.xlsx',sheet_name='Non-Flow')
# inq_nonflow.messages = inq_nonflow.messages.fillna('').apply(lambda x: x.split(','))




# DATABASE
# ************************************************************
def update_chatlog(chatlog):
	last_date = to_datetime(chatlog._date.max())
	yesterday = to_datetime(to_datestr(datetime.datetime.today())) - timedelta(days=1)
	if last_date < yesterday:
		# date_to_query = last_date + timedelta(days=1)
		# client = MongoClient("mongodb+srv://ntlstat:4RBpZqrlUpgKuStd@cluster0-qvbke.mongodb.net/ntlstat")
		# cl = client["ntlstat"]
		murl = "mongodb://heroku_0n2r8pw1:ptuetisq6abh9ec3vhg0idisa8@ds249808-a0.mlab.com:49808,ds249808-a1.mlab.com:49808/heroku_0n2r8pw1?replicaSet=rs-ds249808"
		client = MongoClient(murl)
		dbname = 'heroku_0n2r8pw1'
		cl = client[dbname]
		# agentchatlog = pd.DataFrame(list(cl.agentchatlog.find({"messageDetail.time":{"$gte": to_datestr(date_to_query)}})))
		agentchatlog = pd.DataFrame(list(cl.agentchatlog.find({"messageDetail.time":{"$gte": '2020-05-31 00:00:00'}})))
		chatlog_to_append = pd.DataFrame(columns=['userId','full_name','message','role','_date','_time'])
		for index, dat in agentchatlog.iterrows():
			chatlog_to_append = chatlog_to_append.append(get_chatlog(dat),ignore_index = True,sort=False)
		# chatlog_to_append = chatlog_to_append.loc[to_datetime(chatlog_to_append._date)<=yesterday] 
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

def get_traindata():
	murl = "mongodb://heroku_0n2r8pw1:ptuetisq6abh9ec3vhg0idisa8@ds249808-a0.mlab.com:49808,ds249808-a1.mlab.com:49808/heroku_0n2r8pw1?replicaSet=rs-ds249808"
	client = MongoClient(murl)
	dbname = 'heroku_0n2r8pw1'
	cl = client[dbname]
	nlp_view_record = cl.nlp_view_record
	viewrec = pd.DataFrame(list(nlp_view_record.find({})))
	viewrec['_date'] = viewrec['_credate'].astype('str').str[0:10]
	viewrec['_time'] = viewrec['_credate'].astype('str').str[11:16]

	return viewrec[['_date','_time','Keyword','Intent']]

# EXTRACTION
# ************************************************************

def extract_user_metrics(startdate,enddate):
	print('Start Extracting User Metrics...')
	result = pd.DataFrame(columns = ['Date','Metric','Count'])
	for date in daterange(startdate,enddate):
		printdate = to_dategooglesheet(date)
		date = to_datestr(date)
		# usercount = get_usercount(date)
		# activeusercount = get_activeusercount(date)
		# engagedusercount = get_engagedusercount(date)
		newusercount = get_newusercount(date)
		# result = result.append(pd.Series([printdate,'user',usercount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'active_user',activeusercount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'engaged_user',engagedusercount],index=['Date','Metric','Count']),ignore_index=True)
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
		# msgcount = get_msgcount(date,msg_type='total')
		# inmsgcount = get_msgcount(date,msg_type='user')
		# confusemsgcount = get_confusemsgcount(date)
		# missmsgcount = get_msgcount(date,msg_type='miss')
		# convercount = get_convercount(date)
		# newconvercount = get_untrainmsgcount(date)
		trainmsgcount = get_trainmsgcount(date)
		# result = result.append(pd.Series([printdate,'msg',msgcount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'in_msg',inmsgcount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'confuse_msg',confusemsgcount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'miss_msg',missmsgcount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'conver',convercount],index=['Date','Metric','Count']),ignore_index=True)
		# result = result.append(pd.Series([printdate,'new_conver',newconvercount],index=['Date','Metric','Count']),ignore_index=True)
		result = result.append(pd.Series([printdate,'trained',trainmsgcount],index=['Date','Metric','Count']),ignore_index=True)
		print('Extraction In Progress: %s complete'%date)
	print('====================================Extraction Complete====================================')
	return result

# def extract_bot_metrics(startdate,enddate):
# 	print('Start Extracting Bot Metrics...')
# 	result = pd.DataFrame(columns = ['Date','Metric','Count'])
# 	for date in daterange(startdate,enddate):
# 		printdate = to_dategooglesheet(date)
# 		date = to_datestr(date)
# 		ret30d, ret90d, ret6m, ret1y = get_retentioncount(date)
# 		goalcount_df = get_goalcompletion(date)
# 		goal = goalcount_df.Goal.tolist()
# 		count = goalcount_df.Count.tolist()
# 		converinterval = get_converinterval(date)
# 		converinterval_max, converinterval_median, converinterval_min = max(converinterval), np.median(converinterval), min(converinterval)
# 		convermsg = get_convermsg(date)
# 		convermsg_max, convermsg_median, convermsg_min = max(convermsg), np.median(convermsg), min(convermsg)

# 		result = result.append(pd.Series([printdate,'ret30d',ret30d],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'ret90d',ret90d],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'ret6m',ret6m],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'ret1y',ret1y],index=['Date','Metric','Count']),ignore_index=True)
# 		for i in range(len(goal)):
# 			result = result.append(pd.Series([printdate, goal[i],count[i]],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'converinterval_max',converinterval_max],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'converinterval_median',converinterval_median],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'converinterval_min',converinterval_min],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'convermsg_max',convermsg_max],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'convermsg_median',convermsg_median],index=['Date','Metric','Count']),ignore_index=True)
# 		result = result.append(pd.Series([printdate,'convermsg_min',convermsg_min],index=['Date','Metric','Count']),ignore_index=True)
		
# 		print('Extraction In Progress: %s complete'%date)
# 	print('====================================Extraction Complete====================================')
# 	return result

# def extract_inquiry_flow(startdate, enddate):
# 	print('Start Extracting Inquiry Report (Flow)...')
# 	result = pd.DataFrame(columns=['Date','Flow','State','Key','Description','Count','Drop'])
# 	for date in daterange(startdate,enddate):
# 		printdate = to_dategooglesheet(date)
# 		date = to_datestr(date)
# 		flow_df = get_inq_flow(date)
# 		flow = flow_df['flow'].tolist()
# 		state = flow_df['state'].tolist()
# 		key = flow_df['key'].tolist()
# 		desc = flow_df['description'].tolist()
# 		count = flow_df['count'].tolist()
# 		drop = flow_df['drop'].tolist()
# 		for i in range(len(flow)):
# 			result = result.append(pd.Series([printdate,flow[i],state[i],key[i],desc[i],count[i],drop[i]],index=['Date','Flow','State','Key','Description','Count','Drop']),ignore_index=True)
# 		print('Extraction In Progress: %s complete'%date)
# 	print('====================================Extraction Complete====================================')
# 	return result

# def extract_inquiry_nonflow(startdate, enddate):
# 	print('Start Extracting Inquiry Report (Non-Flow)...')
# 	result = pd.DataFrame(columns=['Date','Flow','State','Key','Description','Count'])
# 	for date in daterange(startdate,enddate):
# 		printdate = to_dategooglesheet(date)
# 		date = to_datestr(date)
# 		nonflow_df = get_inq_nonflow(date)
# 		flow = nonflow_df['flow'].tolist()
# 		state = nonflow_df['state'].tolist()
# 		key = nonflow_df['key'].tolist()
# 		desc = nonflow_df['description'].tolist()
# 		count = nonflow_df['count'].tolist()
# 		for i in range(len(nonflow_df)):
# 			result = result.append(pd.Series([printdate,flow[i],state[i],key[i],desc[i],count[i]],index=['Date','Flow','State','Key','Description','Count']),ignore_index=True)
# 		print('Extraction In Progress: %s complete'%date)
# 	print('====================================Extraction Complete====================================')
# 	return result

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

	# 18.06.2020 requirement changed to get only the new user of the entire time
	# =======================================================================
	# date = datetime.datetime.strptime(date,'%Y-%m-%d')
	# year = date.year
	# month = date.month
	
	# if month == 1:
	# 	year_prev = year - 1
	# 	month_prev = 12
	# else: 
	# 	year_prev = year
	# 	month_prev = month - 1

	# startdate = datetime.datetime(year_prev,month_prev,1).strftime('%Y-%m-%d')
	# enddate = datetime.datetime(year_prev,month_prev,calendar.monthrange(year_prev, month_prev)[1]).strftime('%Y-%m-%d')
	# =======================================================================

	# 18.06.2020 requirement changed to get only the new user of the entire time
	# =======================================================================
	startdate = '2019-11-01'
	enddate = to_datestr(datetime.datetime.strptime(date,'%Y-%m-%d') + relativedelta(days=-1))
	# =======================================================================

	user_prev = get_user_range(startdate,enddate)

	newuser = diff(user,user_prev)

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

def get_dropoutmsgcount(date):
	return len(get_dropoutmsg(date))

# miss_msg
def get_confusemsg(date):
    mask_distance = nlp_dashboard.distance < CONFIDENCE_VALUE
    mask_date = nlp_dashboard._date == date

    return nlp_dashboard.loc[ mask_date & mask_distance ].values.tolist()

def get_confusemsgcount(date):
	return len(get_confusemsg(date))

def get_missmsgcount(date):
    return get_confusemsgcount(date) + get_dropoutmsgcount(date)

# Total conversation (# of conversations completed end-to-end by bot within a day -- engaged users)
def get_conver(date):
	interval = 0
	converpos = 0
	converlist = []
	currentuser = ''
	currentrole = ''
	currenttime = '0:00'
	chatlog_conv = chatlog.loc[chatlog._date==date].sort_values(by=['userId','_time'])
	for index, row in chatlog_conv.iterrows():
		interval = abs(timeinterval(currenttime,row._time))
		if (row.userId != currentuser) | ((row.role=='User')&(interval > CONVERSATION_TIMELIMIT)) | ((row.role=='Admin')&(currentrole=='Admin')&(interval>CONVERSATION_TIMELIMIT)):
			# print(row.userId,interval,converpos)
			currentuser = row.userId
			converpos += 1
		
		currentrole = row.role
		currenttime = row._time
		converlist.append(converpos)
	
	chatlog_conv['conv'] = converlist

	return chatlog_conv

def get_convercount(date):
	chatlog_conv = get_conver(date)
	convercount = chatlog_conv.conv.max()
	return convercount


# New conversation (# of new conversations that are not trained but initiated by users)
def get_untrainmsg(date):
	return nlp_dashboard.loc[(nlp_dashboard.distance<1)&(nlp_dashboard._date==date)].values.tolist()

def get_untrainmsgcount(date):
	return len(get_untrainmsg(date))

# Trained messages
def get_trainmsg(date):
	return traindata.loc[traindata._date==date]

def get_trainmsgcount(date):
	return get_trainmsg(date)._date.count()

# ===========================BOT METRICS================================================
# Retention Rate (% of users that return to use bot)
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

def get_retentionrate(date):
	ret30d, ret90d, ret6m, ret1y = get_retentioncount(date)
	total_user = len(get_user(date))

	return ret30d/total_user, ret90d/total_user, ret6m/total_user, ret1y/total_user

# Goal Completion Rate (# of leads, No. of Engaged users)
def get_goalcompletion(date):
	count = []
	for index, row in goal.iterrows():
		count.append(get_keywordsearch(date,row.Keywords,mode='usercount'))
	goal['Count'] = count
	return goal[['Goal','Count']]

# Goal completion time/messages/taps (Minimizing the effort to complete a goal can improve user experience.) "อยากได้ step ว่าคนเลิกคุยกับ bot ตอนถามคำถามอะไร จะได้นำไปดีไซน์ใหม่"
def get_converinterval(date):
	chatlog_conv = get_conver(date)
	conv_interval = []
	chatlog_conv = chatlog_conv.loc[chatlog_conv.role=='User'].sort_values(by='conv',ascending=True)
	for conv in chatlog_conv.conv.unique().tolist():
		interval = abs(timeinterval(chatlog_conv.loc[chatlog_conv.conv==conv]._time.tolist()[0],chatlog_conv.loc[chatlog_conv.conv==conv]._time.tolist()[-1])).total_seconds()
		conv_interval.append(interval/60)
		# print(conv, interval)
	return conv_interval

def get_convermsg(date):
	chatlog_conv = get_conver(date)
	return chatlog_conv[chatlog_conv.role=='User'].groupby('conv').message.count().tolist()

# Fallback Rate (FBR) (% of chatbot failures happened)



# User-satisfaction (Did the bot perform well? Y/N)

# ===========================OTHER METRICS================================================
# Keyword count
def get_keywordsearch(date, keywordlist, mode='msgcount'):
	if type(keywordlist) != list:
		print("input keywords as a list of strings")
		return None

	dat = botlog.loc[botlog.date==date].copy()
	dat.loc[:,'key'] = 0
	for keyword in keywordlist:
		dat.loc[:,'key_temp']=0
		if keyword != "":
			# print("keyword:", keyword)

			dat.loc[:,'key_temp'] = dat.message.str.contains(keyword).fillna(0).astype(int)
			dat.loc[:,'key'] = dat[['key','key_temp']].max(axis=1)

	if mode == 'uniqueuser':
		return dat.loc[dat.key==1].userId.unique().tolist()
	elif mode == 'user':
		return dat.loc[dat.key==1].userId.tolist()
	elif mode == 'msgcount':
		return dat.loc[dat.key==1].message.count()
	elif mode == 'usercount':
		return len(dat.loc[dat.key==1].userId.unique())
	else:
		return 0

# ===========================INQUIRY REPORTS================================================
# def get_inq_flow(date):
# 	inq_flow = pd.DataFrame(columns=['flow','state','key','description','count','drop'])
# 	inq_flow = inq_flow.append(get_ins_lead(date),ignore_index=True)
	
# 	return inq_flow

# def get_ins_lead(date):
# 	userlist = []
# 	countlist = []
# 	droplist = []
# 	ins_lead = inq_flow.loc[inq_flow.key.str.contains('ins_lead')]
# 	keylist = ins_lead.key.tolist()
# 	keep_count = ins_lead.keep_count.tolist()
# 	keep_drop = ins_lead.keep_drop.tolist()
# 	messagelist = ins_lead.messages.tolist()

# 	# UserId & No. of users
# 	for i in range(len(keylist)):
# 		userlist_row = get_keywordsearch(date,messagelist[i],mode='uniqueuser')
# 		userlist.append(userlist_row)
# 		countlist.append(len(userlist_row)*keep_count[i])
	
# 	ins_lead['user'] = userlist
# 	ins_lead['count'] = countlist

# 	ins10 = ins_lead.loc[ins_lead.key=='ins_lead-10'].user.values[0]
# 	ins11 = ins_lead.loc[ins_lead.key=='ins_lead-11'].user.values[0]
# 	ins101x = ins_lead.loc[ins_lead.key=='ins_lead-10.1x'].user.values[0]

# 	# Dropout ins_lead-00 to ins_lead-10.1x
# 	for i in range(0,12):
# 		droplist.append(len(list(diff(userlist[i],userlist[i+1],unique=True)))*keep_drop[i])

# 	# Dropout ins_lead-10.1	
# 	drop101 = list(intersect(ins101x,diff(ins10,ins11,unique=True),unique=True))
# 	droplist.append(len(drop101))
# 	# Dropout ins_lead-10.2
# 	drop102 = list(diff(diff(ins10,ins11,unique=True),drop101,unique=True))
# 	droplist.append(len(drop102))
# 	# Dropout ins_lead-11
# 	droplist.append(0)
	

# 	ins_lead['drop'] = droplist

# 	ins_lead['flow'] = ins_lead['key'].apply(lambda x: x.split('-')[0])
# 	ins_lead['state'] = ins_lead['key'].apply(lambda x: x.split('-')[1])

# 	# Remove the entries used for calculations
# 	ins_lead = ins_lead.loc[(ins_lead.keep_count==1)|(ins_lead.keep_drop==1)]

# 	return ins_lead[['flow','state','key','description','count','drop']]

# def get_inq_nonflow(date, inq_nonflow=inq_nonflow):
# 	userlist = []
# 	countlist = []
# 	keylist = inq_nonflow.key.tolist()
# 	messagelist = inq_nonflow.messages.tolist()

# 	# No. of messages / transactions
# 	for i in range(len(keylist)):
# 		# non-unique users = transaction count
# 		userlist.append(get_keywordsearch(date,messagelist[i],mode='user'))
# 		countlist.append(len(userlist[i]))

# 	inq_nonflow['user'] = userlist
# 	inq_nonflow['count'] = countlist

# 	# Calc loan_t-03
# 	lt01x = inq_nonflow.loc[inq_nonflow.key=='loan_t-01x'].user.values[0]
# 	lt02x = inq_nonflow.loc[inq_nonflow.key=='loan_t-02x'].user.values[0]
# 	lt03x = inq_nonflow.loc[inq_nonflow.key=='loan_t-03x'].user.values[0]

# 	lt03 = intersect(intersect(lt01x,lt02x,unique=False),lt03x,unique=False)

# 	# Calc loan_t-04
# 	lt04x = inq_nonflow.loc[inq_nonflow.key=='loan_t-04x'].user.values[0]

# 	lt04 = intersect(lt03x,lt04x,unique=False)

# 	# Calc loan_t-05.2
# 	lt05 = inq_nonflow.loc[inq_nonflow.key=='loan_t-05.2'].user.values[0]
# 	lt052x = inq_nonflow.loc[inq_nonflow.key=='loan_t-05.2x'].user.values[0]
# 	lt052x2 = inq_nonflow.loc[inq_nonflow.key=='loan_t-05.2x2'].user.values[0]

# 	lt052 = intersect(lt03x,lt052x,unique=False)

# 	# Calc loan_c-04
# 	lm04 = inq_nonflow.loc[inq_nonflow.key=='loan_m-04'].user.values[0]

# 	lc04 = diff(lt04x,lt04,unique=False)

# 	# Replace counts into the dataframe
# 	inq_nonflow.loc[inq_nonflow.key=='loan_t-03','count'] = len(lt03)
# 	inq_nonflow.loc[inq_nonflow.key=='loan_t-04','count'] = len(lt04)
# 	inq_nonflow.loc[inq_nonflow.key=='loan_t-05.2','count'] = len(lt052)
# 	inq_nonflow.loc[inq_nonflow.key=='loan_c-04','count'] = len(lc04)

# 	# # Remove the count of entries used for calculations
# 	# inq_nonflow.loc[inq_nonflow.keep_count==0,'count'] = 0

# 	inq_nonflow['flow'] = inq_nonflow['key'].apply(lambda x: x.split('-')[0])
# 	inq_nonflow['state'] = inq_nonflow['key'].apply(lambda x: x.split('-')[1])

# 	# Remove the entries used for calculations
# 	inq_nonflow = inq_nonflow.loc[inq_nonflow.keep_count==1]

# 	return inq_nonflow[['flow','state','key','description','count']]


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

def diff(list1, list2, unique = False):
	if (list1 == []):
		return []
	elif list2 == []:
		return list1
	list1 = np.array(list1)
	list2 = np.array(list2)
	if unique:
		res = list(np.setdiff1d(list1,list2))
	else: 
		res = [x for x in list1 if x not in list2]
	return res

def intersect(list1, list2, unique = False):
	if (list1 == []) or (list2 == []):
		return []	
	list1 = np.array(list1)
	list2 = np.array(list2)
	if unique:
		res = list(np.intersect1d(list1,list2))
	else: 
		res = [x for x in list1 if x in list2]
	return res

def clean_chatlog(chat):
	chat = chat.loc[chat.userId!='facebook'] 
	chat = chat.loc[chat.userId!='1379039449007314']
	return chat

print('read chatlog ..')
chatlog = pd.read_pickle('../data/chatlog.p')
# print('update chatlog ..')
# chatlog = update_chatlog(chatlog)

print('clean chatlog ..')
chatlog = clean_chatlog(chatlog)

print('read trained data ..')
traindata = get_traindata()

print('read nlp_dashboard ..')
nlp_dashboard = pd.read_pickle('../data/nlp_dashboard.p')

print('read submit_to_agent ..')
submit_to_agent = pd.read_pickle('../data/submit_to_agent.p')

print('format date ..')

chatlog['date'] = chatlog._date

nlp_dashboard['_date'] = nlp_dashboard['date'].astype('str').str[0:10]
nlp_dashboard['distance'] = pd.to_numeric(nlp_dashboard['distance'])

submit_to_agent['_date'] = submit_to_agent['datetime'].astype('str').str[0:10]

print('reformat message to str ..')
chatlog.message = chatlog.message.astype(str)

print('create botlog/userlog dataframes ..')
botlog = chatlog.loc[chatlog.role=='Admin'].copy()
userlog = chatlog.loc[chatlog.role=='User'].copy()