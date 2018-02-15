#!/usr/bin/env python
# encoding: utf-8

# Initialize
import json
import boto3
import datetime
import requests
import os

servicenames = ['AmazonCloudWatch','AmazonEC2','AmazonRoute53','AmazonS3','AmazonSNS','AWSCodeCommit','AWSDataTransfer','awskms','AWSLambda','AWSMarketplace','AWSQueueService']

totalcost = 0.0
getcost = 0.0
sndcoststr = ''
getdate = ''

res = boto3.client('cloudwatch', region_name='us-east-1')

# Get ENV
SLACK_POST_URL = os.environ['SlackPostURL']
SLACK_CHANNEL = os.environ['SlackChannelName']

# Get Estimated Charges by service
for srvname in servicenames:
	gms = res.get_metric_statistics(
	  Namespace='AWS/Billing',
	  MetricName='EstimatedCharges',
	  Dimensions=[
	    {
	    'Name': 'Currency',
	    'Value': 'USD'
	    },
	    {
	    'Name': 'ServiceName',
	    'Value': srvname
	    }
	  ],
	  StartTime=datetime.datetime.today() - datetime.timedelta(days=1),
	  EndTime=datetime.datetime.today(),
	  Period=86400,
	  Statistics=['Maximum'])

	if len(gms['Datapoints']) > 0:
		getcost = gms['Datapoints'][0]['Maximum']
		getdate = gms['Datapoints'][0]['Timestamp'].strftime('%Y/%m/%d %H:%M')
	else:
		getcost = 0.0
	coststr = u"%s: %s  USD\n" % (srvname,"{:.2f}".format(getcost))
	sndcoststr = sndcoststr + coststr

# Get Estimated Total Charge
gms = res.get_metric_statistics(
  Namespace='AWS/Billing',
  MetricName='EstimatedCharges',
  Dimensions=[
    {
    'Name': 'Currency',
    'Value': 'USD'
    }
  ],
  StartTime=datetime.datetime.today() - datetime.timedelta(days=1),
  EndTime=datetime.datetime.today(),
  Period=86400,
  Statistics=['Maximum'])

if len(gms['Datapoints']) > 0:
	totalcost = gms['Datapoints'][0]['Maximum']
else:
	totalcost = 0.0

# Make message for send to Slack
sndstr = '**************************************************' + "\n"
sndstr = sndstr + 'AWS Estimated Cost Report on ' + getdate + " UTC \n"
sndstr = sndstr + '**************************************************' + "\n"
sndstr = sndstr + sndcoststr
str = u"TOTAL: %s USD" % ("{:.2f}".format(totalcost))
sndstr = sndstr + '**************************************************' + "\n"
sndstr = sndstr + str + "\n"
sndstr = sndstr + '**************************************************' + "\n"

def lambda_handler(event, context):
	sendmsg = {"text":sndstr}
	send_message = {'channel': SLACK_CHANNEL, "attachments": [sendmsg]}
	req = requests.post(SLACK_POST_URL, data=json.dumps(send_message))
