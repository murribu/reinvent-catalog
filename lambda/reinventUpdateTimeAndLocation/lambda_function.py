import json
import requests
import boto3
import os
from datetime import datetime
from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
	retval = []

	message = {"foo": "bar"}
	client = boto3.client('sns')
	response = client.publish(
		TargetArn=os.environ["sns_arn"],
		Message=json.dumps({'default': json.dumps(message),
			'sms': "start!",
			'email': "start!"}),
		Subject='The Reinvent UpdateTimeAndLocation process has started',
		MessageStructure='json'
	)

	dynamo = boto3.resource('dynamodb')
	table = dynamo.Table(os.environ["dynamotable"])

	response = table.scan(ProjectionExpression="id,title,starttime,endtime,room")


	for i in response["Items"]:
		session_id = i["id"][8:]

		headers = {
			'pragma': 'no-cache' ,
			'cookie': 'DWRSESSIONID=NVvTRf5b4szMSFIGZR8sKQXfAqm; _ga=GA1.2.603512740.1498063034; s_fid=4DF3153FC00FF9A8-00D998B2CA4F09CE; regStatus=pre-register; session-set=true; aws-priv=eyJ2IjoxLCJzdCI6MX0=; __atssc=google%3B2; s_vn=1561578928706%26vn%3D7; s_dslv=1539638781939; s_nr=1539638781943-Repeat; cookieAgreement=agreed; SESSIONIDconnect=aaaGp_I9wRPerb548ZgBw; AWSALB=TLzJohSUKCvDwcNcP//2tjBnOWvFF7laoAKPyoUKH5shGiLHNURdy+JHMDGxHs5qpLI91Q3+LQHm+DT8KWEhiuDH0aEg1grS+Jwa/1YDLi38wCi7jObQ+qBMBGt9w/IU5Gr1TBpw5aMnibjsA0v1C3sOOi3QkTN3Oau3nDf18KF311tjr/9R+vXCoDWcdA==; __atuvc=0%7C40%2C38%7C41%2C22%7C42%2C4%7C43%2C10%7C44; __atuvs=5bd8c8a9cff3d930006' ,
			'origin': 'https://www.portal.reinvent.awsevents.com' ,
			'accept-encoding': 'gzip, deflate, br' ,
			'accept-language': 'en-US,en;q=0.9' ,
			'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36' ,
			'content-type': 'text/plain' ,
			'accept': '*/*' ,
			'cache-control': 'no-cache' ,
			'authority': 'www.portal.reinvent.awsevents.com' ,
			'referer': 'https://www.portal.reinvent.awsevents.com/connect/sessionDetail.ww?SESSION_ID=' + session_id + '&tclass=popup'
		}
		data = 'callCount=1\nwindowName=\nc0-scriptName=ConnectAjax\nc0-methodName=getSchedulingJSON\nc0-id=0\nc0-param0=number:' + session_id + '\nc0-param1=boolean:false\nbatchId=1\ninstanceId=0\npage=%2Fconnect%2FsessionDetail.ww%3FSESSION_ID%3D' + session_id + '%26tclass%3Dpopup\nscriptSessionId=NVvTRf5b4szMSFIGZR8sKQXfAqm/SpET7rm-3Xhjxhtio\n'

		page = requests.post("https://www.portal.reinvent.awsevents.com/connect/dwr/call/plaincall/ConnectAjax.getSchedulingJSON.dwr", headers=headers, data=data)

		content = BeautifulSoup(page.text, 'html.parser')

		s3 = boto3.client('s3')
		s3.put_object(Body=page.text, Bucket='reinvent-grabs', Key=session_id + '.html')

		funcCall = page.text.split('\n')[5]
		data = funcCall[37:-4]
		data = data.replace("\\\"","\"")
		obj = json.loads(data)

		needsUpdating = False
		updateExpression = 'Set updated_at = :updated_at,'
		expressionAttributeValues = {
			':updated_at': str(datetime.now())
		}

		hasStartTime = True
		try:
			i["starttime"]
		except KeyError:
			hasStartTime = False

		if (not hasStartTime) or (obj[0]["startTime"] != i["starttime"]):
			updateExpression += 'starttime = :starttime,'
			expressionAttributeValues[':starttime'] = obj[0]["startTime"]
			needsUpdating = True

		hasEndTime = True
		try:
			i["endtime"]
		except KeyError:
			hasEndTime = False

		if (not hasEndTime) or (obj[0]["endTime"] != i["endtime"]):
			updateExpression += 'endtime = :endtime,'
			expressionAttributeValues[':endtime'] = obj[0]["endTime"]
			needsUpdating = True

		hasRoom = True
		try:
			i["room"]
		except KeyError:
			hasRoom = False

		if (not hasRoom) or (obj[0]["room"] != i["room"]):
			updateExpression += 'room = :room,'
			expressionAttributeValues[':room'] = obj[0]["room"]
			needsUpdating = True

		if needsUpdating:
			message = {"previous": i, "new": obj}
			client = boto3.client('sns')
			response = client.publish(
				TargetArn=os.environ["sns_arn"],
				Message=json.dumps({'default': json.dumps(message),
					'sms': i["id"] + " has changed!",
					'email': i["id"] + " has changed!"}),
				Subject=i["id"] + " has changed!",
				MessageStructure='json'
			)
			table.update_item(
				Key={ 'id': i["id"] },
				UpdateExpression=updateExpression[:-1],
				ExpressionAttributeValues=expressionAttributeValues
			)
		# [{"action": null, "imageStyle": "imageAddDisabled", "message": "You must log in to schedule.", "startTime": "Thursday, Nov 29, 12:15 PM", "endTime": "2:30 PM", "room": "Venetian, Level 4, Lando 4205", "roomId": 1984, "mapId": 0, "sessionTimeID": 16973}]]

	message = {"foo": "bar"}
	client = boto3.client('sns')
	response = client.publish(
		TargetArn=os.environ["sns_arn"],
		Message=json.dumps({'default': json.dumps(message),
			'sms': "stop!",
			'email': "stop!"}),
		Subject='The Reinvent UpdateTimeAndLocation process has finished!',
		MessageStructure='json'
	)

	return page.text