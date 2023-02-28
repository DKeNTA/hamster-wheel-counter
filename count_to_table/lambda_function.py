import json
import boto3
import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('counter-table')

def lambda_handler(event, context):
    #print(json.dumps(event))
    posted_param = json.loads(event['body'])
    
    year = posted_param['year'] 
    month = posted_param['month'] 
    day = posted_param['day'] 
    hour = posted_param['hour'] 
    count = posted_param['count'] 
    
    dt = datetime.datetime(year, month, day, hour)
    
    table.put_item(
    	Item={
    		"date": dt.strftime('%Y%m%d'),
    		"time": dt.strftime('%H'),
    		"count": count
    	}
    )
    
    return {
        "statusCode": 200,
        'body': json.dumps('Success!')
    }
    
