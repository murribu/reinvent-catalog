import json
import requests
import boto3
import os
from bs4 import BeautifulSoup
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(os.environ["dynamotable"])

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

    retval.append(headers["cookie"])

    data = {"searchPhrase": "", "searchType": "session", "tc": "0", "sortBy": "abbreviationSort", "p": ""}
    page = requests.post("https://www.portal.reinvent.awsevents.com/connect/processSearchFilters.do", headers=headers, data=data)
    
    content = BeautifulSoup(page.text, 'html.parser')
    
    s3 = boto3.client('s3')
    s3.put_object(Body=page.text, Bucket='reinvent-grabs', Key='1.html')
        
    resultRows = content.select('.resultRow')

    for resultRow in resultRows:
        speakers = str(''.join(map(str,resultRow.find_all("small", {"class": "speakers"})[0].contents)))
        speakers = speakers if speakers != "" else " "
        track = str(''.join(map(str,resultRow.find_all("span", {"class": "track"})[0].contents)))
        track = track if track != "" else " "
        row_data = {
            'id': resultRow.attrs["id"],
            'abbr': resultRow.find("span", {"class": "abbreviation"}).string.strip(),
            'title': resultRow.find("span", {"class": "title"}).string.strip(),
            'abstract': resultRow.find("span", {"class": "abstract"}).string.strip(),
            'session_type': resultRow.find("small", {"class": "type"}).string.strip(),
            'speakers': speakers,
            'track': track,
            # "html": str(resultRow)
        }
        # if len(str(resultRow.find_all("small", {"class": "speakers"})[0])) > 32:
        #     return str(''.join(map(str,resultRow.find_all("small", {"class": "speakers"})[0].contents)))
        response = table.query(KeyConditionExpression=Key('id').eq(row_data["id"]))
        items = response['Items']
        if len(items) == 0:
            table.put_item(Item=row_data)
        else:
            table.update_item(
                Key={ 'id': row_data["id"] },
                UpdateExpression='Set abbr = :abbr, title = :title, abstract = :abstract, session_type = :session_type, speakers = :speakers, track = :track',
                ExpressionAttributeValues={
                    ':abbr': row_data['abbr'],
                    ':title': row_data['title'],
                    ':abstract': row_data['abstract'],
                    ':session_type': row_data['session_type'],
                    ':speakers': row_data['speakers'],
                    ':track': row_data['track'],
                }
            )

    #second call

    awsalb = ''
    sessionidconnect = ''
    for entry in page.headers['Set-Cookie'].split('; '):
        retval.append(entry.split('=')[0])
        if (entry.split('=')[0] == 'AWSALB'):
            awsalb = entry.split('=')[1]
        if (entry.split('=')[0] == 'Path' and entry.split('=')[1] == '/, SESSIONIDconnect'):
            sessionidconnect = entry.split('=')[2]

    headers["cookie"] = "DWRSESSIONID=nNNQ8ZylsbVlrLX1TUpsMzSNppm; _ga=GA1.2.603512740.1498063034; s_fid=4DF3153FC00FF9A8-00D998B2CA4F09CE; regStatus=pre-register; session-set=true; aws-priv=eyJ2IjoxLCJzdCI6MX0=; __atssc=google%3B1; s_campaign=em%7Cawsreinvent_reg_reminder%7Cem_84172%7Cevent_ev_reinvent%7Cevent%7Cglobal%7Cmult%7Cem_84172; c_m=emundefinedEmailundefined; s_cc=true; s_eVar60=em_84172; cookieAgreement=agreed; SESSIONIDportal=aaaZC9WE1bIhL_m8YXzzw; s_vn=1561578928706%26vn%3D5; s_sq=%5B%5BB%5D%5D; s_dslv=1539197425868; s_nr=1539197425870-Repeat; SESSIONIDconnect=" + sessionidconnect + "; __atuvc=0%7C37%2C0%7C38%2C0%7C39%2C0%7C40%2C34%7C41; __atuvs=5bc2a4f5bfc9bf9e000; AWSALB=" + awsalb

    retval.append(headers["cookie"])
    
    data = {"searchType": "session", "more": "true"}
    page = requests.post("https://www.portal.reinvent.awsevents.com/connect/processSearchFilters.do", headers=headers, data=data)
    
    s3 = boto3.client('s3')
    s3.put_object(Body=page.text, Bucket='reinvent-grabs', Key='2.html')

    return retval