import pandas as pd
import pymongo
from pymongo import MongoClient
import numpy as np
import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

# Format time to match with the data
today = date.today()
td = today.strftime("%Y-%m-%d")

# Read ad_id data
ad_id = pd.read_csv('../excel/ad_id.csv')

# Read chatlog data
chatlog = pd.read_csv('../excel/chatlog.csv')


def get_user(date):
	userlist = chatlog.loc[chatlog._date==date].userId.tolist()
	return list(set(userlist))


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


def get_users_channel(date: str, ad_id, chatlog):
    ad_id.drop_duplicates(subset='sender_id', keep='last', inplace=True)
    ad_users = ad_id.loc[ad_id.ad_id.notnull()]
    ref_users = ad_id.loc[ad_id.ref.notnull()]
    ad_users = ad_users.loc[ad_users.date.str.startswith(date)].sender_id.unique().tolist()
    ref_users = ref_users.loc[ref_users.date.str.startswith(date)].sender_id.unique().tolist()
    total_users = get_user(date)
    in_ad_users = intersect(total_users, ad_users)
    in_ref_users = intersect(total_users, ref_users)
    org_users = list(set(total_users) - set(ad_users) - set(ref_users))
    return (org_users, in_ad_users, in_ref_users)


def get_inq_flow(date):
    inq_flow = pd.DataFrame(columns=['flow','state','key','description', 'count','organic_count', 'ad_count', 'ref_count', 'drop'])
    inq_flow = inq_flow.append(get_ins_lead(date),ignore_index=True)

    return inq_flow

# Keyword count
def get_keywordsearch(date, keywordlist, mode='msgcount'):
    if type(keywordlist) != list:
        print("input keywords as a list of strings")
        return None

    dat = botlog.loc[botlog._date==date].copy()
    dat.loc[:,'key'] = 0
    for keyword in keywordlist:
        dat.loc[:,'key_temp']=0
        if keyword != "":
    # 			print("keyword:", keyword)

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

def get_ins_lead(date):
    userlist = []
    countlist = []
    droplist = []
    org_countlist = []
    ad_countlist = []
    ref_countlist = []
    org_droplist = []
    ad_droplist = []
    ref_droplist = []
    org_userlist, ad_userlist, ref_userlist = get_users_channel(date, ad_id, chatlog)
#     orglist = []
#     adlist = []
#     reflist = []
    ins_lead = inq_flow.loc[inq_flow.key.str.contains('ins_lead')]
    keylist = ins_lead.key.tolist()
    keep_count = ins_lead.keep_count.tolist()
    keep_drop = ins_lead.keep_drop.tolist()
    messagelist = ins_lead.messages.tolist()

    # UserId & No. of users
    for i in range(len(keylist)):
        userlist_row = get_keywordsearch(date,messagelist[i],mode='uniqueuser')
        userlist.append(userlist_row)
        orglist.append(intersect(org_userlist, userlist))
        adlist.append(intersect(ad_userlist, userlist))
        reflist.append(intersect(ref_userlist, userlist))
        countlist.append(len(userlist_row)*keep_count[i])
        org_countlist.append(len(intersect(org_userlist, userlist_row))*keep_count[i])
        ad_countlist.append(len(intersect(ad_userlist, userlist_row))*keep_count[i])
        ref_countlist.append(len(intersect(ref_userlist, userlist_row))*keep_count[i])

    ins_lead['user'] = userlist
    ins_lead['count'] = countlist
    ins_lead['organic_user'] = orglist
    ins_lead['organic_count'] = org_countlist
    ins_lead['ad_user'] = adlist
    ins_lead['ad_count'] = ad_countlist
    ins_lead['ref_user'] = reflist
    ins_lead['ref_count'] = ref_countlist

    ins10 = ins_lead.loc[ins_lead.key=='ins_lead-10'].user.values[0]
    ins11 = ins_lead.loc[ins_lead.key=='ins_lead-11'].user.values[0]
    ins101x = ins_lead.loc[ins_lead.key=='ins_lead-10.1x'].user.values[0]

    # Dropout ins_lead-00 to ins_lead-10.1x
    for i in range(0,12):
        droplist.append(len(list(diff(userlist[i],userlist[i+1],unique=True)))*keep_drop[i])

    # Dropout ins_lead-10.1	
    drop101 = list(intersect(ins101x,diff(ins10,ins11,unique=True),unique=True))
    droplist.append(len(drop101))
    # Dropout ins_lead-10.2
    drop102 = list(diff(diff(ins10,ins11,unique=True),drop101,unique=True))
    droplist.append(len(drop102))
    # Dropout ins_lead-11
    droplist.append(0)


    ins_lead['drop'] = droplist

    ins_lead['flow'] = ins_lead['key'].apply(lambda x: x.split('-')[0])
    ins_lead['state'] = ins_lead['key'].apply(lambda x: x.split('-')[1])

    # Remove the entries used for calculations
    ins_lead = ins_lead.loc[(ins_lead.keep_count==1)|(ins_lead.keep_drop==1)]

    return ins_lead[['flow','state','key','description', 'count', 'organic_count', 'ad_count', 'ref_count', 'drop']]


inq_flow = pd.read_excel('../excel/inquiry_report.xlsx',sheet_name='Flow')
inq_flow.messages = inq_flow.messages.fillna('').apply(lambda x: x.split(','))

botlog = chatlog.loc[chatlog.role=='Admin'].copy()
