#!/usr/bin/env python
# encoding: utf-8

# Initialize
import json
import boto3
import datetime
import requests
import logging
import os

from boto3 import Session
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

alltotalsize = 0
alltotalobjcount = 0
bknames = []
bksizemb = {}
objcounts = {}

s3c = Session().client('s3')

# Get ENV
SLACK_POST_URL = os.environ['SlackPostURL']
SLACK_CHANNEL = os.environ['SlackChannelName']

# Get Bucket List
resb = s3c.list_buckets()

# Get Date & Time
nowdtm = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# Put bucket list into list 'bks'
if 'Buckets' in resb:
	bks = [contents['Name'] for contents in resb['Buckets']]

# Get Object size and calculate total size of all objects on every buckets
for bkname in bks:

	nctoken = ''
	totalsize = 0
	objcount = 0

	while 1:
		if nctoken == '':
			resobj = s3c.list_objects_v2(Bucket = bkname)
		else:
			resobj = s3c.list_objects_v2(Bucket = bkname,ContinuationToken = nctoken)
		nctoken = ''
		if 'Contents' in resobj:
			filesizes = [contents['Size'] for contents in resobj['Contents']]
			for filesize in filesizes:
				totalsize = totalsize + filesize
				objcount = objcount + 1
		if 'NextContinuationToken' in resobj:
			nctoken = resobj['NextContinuationToken']
		if nctoken == '':
			break
	totalsizemb = int(totalsize/1024/1024)
	alltotalsize = alltotalsize + totalsizemb
	bknames.append(bkname)
	bksizemb[bkname] = totalsizemb
	objcounts[bkname] = objcount
	alltotalobjcount = alltotalobjcount + objcount

# Make message for send to Slack
sndstr = '**************************************************' + "\n"
sndstr = sndstr + 'AWS S3 Usage Report on ' + nowdtm + " UTC \n"
sndstr = sndstr + '**************************************************' + "\n"

for bknm in bknames:
	if objcounts[bknm] < 2:
		str = u"%s - %s MB (%s object))" % (bknm,bksizemb[bknm],objcounts[bknm])
	else:
		str = u"%s - %s MB (%s object(s))" % (bknm,bksizemb[bknm],objcounts[bknm])
	sndstr = sndstr + str + "\n"
sndstr = sndstr + "\n"
if alltotalobjcount < 2:
	str = u"TOTAL: %s MB (%s object)" % (alltotalsize,alltotalobjcount)
else:
	str = u"TOTAL: %s MB (%s objects)" % (alltotalsize,alltotalobjcount)
sndstr = sndstr + '**************************************************' + "\n"
sndstr = sndstr + str + "\n"
sndstr = sndstr + '**************************************************' + "\n"


def lambda_handler(event, context):
	sendmsg = {"text":sndstr}
	send_message = {'channel': SLACK_CHANNEL, "attachments": [sendmsg]}
	req = requests.post(SLACK_POST_URL, data=json.dumps(send_message))
