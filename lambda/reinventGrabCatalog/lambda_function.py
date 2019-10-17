import json
import requests
import boto3
import os
from datetime import datetime
from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(os.environ["dynamotable"])

    sessionTypeIDs = ['2523', '2832', '2', '1440', '1040', '1560', '2623', '2624', '1921', '2823', '3323', '2834', '2723', '2828']
    retval = []

    headers = {
        "origin": "https://www.portal.reinvent.awsevents.com",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "x-requested-with": "XMLHttpRequest",
        "cookie": "DWRSESSIONID=nNNQ8ZylsbVlrLX1TUpsMzSNppm; _ga=GA1.2.603512740.1498063034; s_fid=4DF3153FC00FF9A8-00D998B2CA4F09CE; regStatus=pre-register; session-set=true; aws-priv=eyJ2IjoxLCJzdCI6MX0=; __atssc=google%3B1; s_campaign=em%7Cawsreinvent_reg_reminder%7Cem_84172%7Cevent_ev_reinvent%7Cevent%7Cglobal%7Cmult%7Cem_84172; c_m=emundefinedEmailundefined; s_cc=true; s_eVar60=em_84172; cookieAgreement=agreed; SESSIONIDportal=aaaZC9WE1bIhL_m8YXzzw; s_vn=1561578928706%26vn%3D5; s_sq=%5B%5BB%5D%5D; s_dslv=1539197425868; s_nr=1539197425870-Repeat; SESSIONIDconnect=aaaI9fba93AVs6fIdvWzw; __atuvc=0%7C37%2C0%7C38%2C0%7C39%2C0%7C40%2C34%7C41; __atuvs=5bc2a4f5bfc9bf9e000; AWSALB=uE/IFAtCKBrwps60hK5TNsa/2/V1iKh5OfQyuY8MWP3d6deS8aND4BV+8b1Kaikj5/BZ6hZoCMjYVC+2+a8LuIQApk9tslhBkwOFxHZYAsr2HqLDU2qughl4OBy/FCwHBFO6uW+OBIN33JjnqidtzcfplB8Mz51XLhcaY/Wy0RXj0BZ5QN3Av2wcSoxSfw==",
        "pragma": "no-cache",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "accept": "*/*",
        "cache-control": "no-cache",
        "authority": "www.portal.reinvent.awsevents.com",
        "referer": "https://www.portal.reinvent.awsevents.com/connect/search.ww"
    }

    # retval.append(headers["cookie"])

    i = 1
    for sessionTypeID in sessionTypeIDs:
        data = {"searchPhrase": "", "searchType": "session", "tc": "0", "sortBy": "abbreviationSort", "p": "", "sessionTypeID": sessionTypeID}
        page = requests.post("https://www.portal.reinvent.awsevents.com/connect/processSearchFilters.do", headers=headers, data=data)
        
        content = BeautifulSoup(page.text, 'html.parser')
        
        s3 = boto3.client('s3')
        # s3.put_object(Body=page.text, Bucket='reinvent-grabs', Key='1.html')
            
        processContentAndSave(table, content)

        #second call

        keepLooping = True
        while keepLooping:
            i += 1
            awsalb = ''
            # sessionidconnect = ''
            retval.append("\ni = %d" % i)
            retval.append(page.headers['Set-Cookie'])
            for entry in page.headers['Set-Cookie'].split('; '):
                # retval.append(entry.split('=')[0])
                if (entry.split('=')[0] == 'AWSALB'):
                    awsalb = entry.split('=')[1]
                if (entry.split('=')[0] == 'Path' and entry.split('=')[1] == '/, SESSIONIDconnect'):
                    sessionidconnect = entry.split('=')[2]

            headers["cookie"] = "DWRSESSIONID=nNNQ8ZylsbVlrLX1TUpsMzSNppm; _ga=GA1.2.603512740.1498063034; s_fid=4DF3153FC00FF9A8-00D998B2CA4F09CE; regStatus=pre-register; session-set=true; aws-priv=eyJ2IjoxLCJzdCI6MX0=; __atssc=google%3B1; s_campaign=em%7Cawsreinvent_reg_reminder%7Cem_84172%7Cevent_ev_reinvent%7Cevent%7Cglobal%7Cmult%7Cem_84172; c_m=emundefinedEmailundefined; s_cc=true; s_eVar60=em_84172; cookieAgreement=agreed; SESSIONIDportal=aaaZC9WE1bIhL_m8YXzzw; s_vn=1561578928706%26vn%3D5; s_sq=%5B%5BB%5D%5D; s_dslv=1539197425868; s_nr=1539197425870-Repeat; SESSIONIDconnect=" + sessionidconnect + "; __atuvc=0%7C37%2C0%7C38%2C0%7C39%2C0%7C40%2C34%7C41; __atuvs=5bc2a4f5bfc9bf9e000; AWSALB=" + awsalb

            # retval.append(headers["cookie"])
            
            data = {"searchType": "session", "more": "true"}
            page = requests.post("https://www.portal.reinvent.awsevents.com/connect/processSearchFilters.do", headers=headers, data=data)

            content = BeautifulSoup(page.text, 'html.parser')
            
            s3 = boto3.client('s3')
            # s3.put_object(Body=page.text, Bucket='reinvent-grabs', Key='%d.html' % i)

            row_count = processContentAndSave(table, content)
            retval.append('row_count = %d' % row_count)
            keepLooping = row_count > 0

    return retval

def processContentAndSave(table, content):
    resultRows = content.select('.resultRow')
    client = boto3.client('sns')

    for resultRow in resultRows:
        speakers = str(''.join(map(str,resultRow.find_all("small", {"class": "speakers"})[0].contents)))
        speakers = speakers if speakers != "" else " "
        track = str(''.join(map(str,resultRow.find_all("span", {"class": "track"})[0].contents)))
        track = track if track != "" else " "
        row_data = {
            'id': resultRow.attrs["id"],
            'abbr': resultRow.find("span", {"class": "abbreviation"}).string.strip(),
            'title': (resultRow.find("span", {"class": "title"}).string or "").strip(),
            'abstract': (resultRow.find("span", {"class": "abstract"}).string or "").strip(),
            'session_type': (resultRow.find("small", {"class": "type"}).string or "").strip(),
            'speakers': speakers,
            'track': track,
            # "html": str(resultRow)
        }
        print(row_data['id'])
        # if len(str(resultRow.find_all("small", {"class": "speakers"})[0])) > 32:
        #     return str(''.join(map(str,resultRow.find_all("small", {"class": "speakers"})[0].contents)))
        response = table.query(KeyConditionExpression=Key('id').eq(row_data["id"]))
        items = response['Items']
        if len(items) == 0:
            row_data['created_at'] = str(datetime.now())
            row_data['updated_at'] = str(datetime.now())
            table.put_item(Item=row_data)
            message = {"new": row_data}
            emailSubject = ("NEW " + row_data["session_type"] + ": "+ row_data["title"])[0:99]
            abbr_end_index = -1
            try:
                abbr_end_index = row_data["abbr"].index('-')
            except:
                abbr_end_index = -1
            messageStr = "New " + row_data["session_type"] + ": " + row_data["title"] + "\nhttps://www.portal.reinvent.awsevents.com/connect/search.ww#loadSearch-searchPhrase=" + (row_data["abbr"]).strip()[0:abbr_end_index].strip() + "&searchType=session&tc=0&sortBy=abbreviationSort&p="
            response = client.publish(
                TargetArn=os.environ["sns_arn"],
                Message=json.dumps({'default': json.dumps(message),
                    'sms': emailSubject,
                    'email': messageStr }),
                Subject=emailSubject,
                MessageStructure='json'
            )
        else:
            needsUpdating = False
            emailMessage = ''
            if items[0]['abbr'] != row_data['abbr']:
                # needsUpdating = True
                emailMessage += 'The abbr changed from ' + items[0]['abbr'] + ' to ' + row_data['abbr'] + '\n'
            if items[0]['title'] != row_data['title']:
                # needsUpdating = True
                emailMessage += 'The title changed from ' + items[0]['title'] + ' to ' + row_data['title'] + '\n'
            if items[0]['abstract'] != row_data['abstract']:
                # needsUpdating = True
                emailMessage += 'The abstract changed from ' + items[0]['abstract'] + ' to ' + row_data['abstract'] + '\n'
            if items[0]['session_type'] != row_data['session_type']:
                needsUpdating = True
                emailMessage += 'The session_type changed from ' + items[0]['session_type'] + ' to ' + row_data['session_type'] + '\n'
            if items[0]['speakers'] != row_data['speakers']:
                # needsUpdating = True
                emailMessage += 'The speakers changed from ' + items[0]['speakers'] + ' to ' + row_data['speakers'] + '\n'
            if items[0]['track'] != row_data['track']:
                # needsUpdating = True
                emailMessage += 'The track changed from ' + items[0]['track'] + ' to ' + row_data['track'] + '\n'

            if needsUpdating:
                message = {"previous": items[0], "new": row_data}
                client = boto3.client('sns')
                emailSubject=("CLASS CHANGE: " + items[0]["title"])[0:99]
                response = client.publish(
                    TargetArn=os.environ["sns_arn"],
                    Message=json.dumps({'default': json.dumps(message),
                        'sms': emailSubject,
                        'email': emailMessage }),
                    Subject=emailSubject,
                    MessageStructure='json'
                )
                table.update_item(
                    Key={ 'id': row_data["id"] },
                    UpdateExpression='Set abbr = :abbr, title = :title, abstract = :abstract, session_type = :session_type, speakers = :speakers, track = :track, updated_at = :updated_at',
                    ExpressionAttributeValues={
                        ':abbr': row_data['abbr'],
                        ':title': row_data['title'],
                        ':abstract': row_data['abstract'],
                        ':session_type': row_data['session_type'],
                        ':speakers': row_data['speakers'],
                        ':track': row_data['track'],
                        ':updated_at': str(datetime.now())
                    }
                )

    return len(resultRows)