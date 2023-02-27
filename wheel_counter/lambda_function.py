import os, sys
import boto3
from boto3.dynamodb.conditions import Key
import json
import calendar
import datetime as dt
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)
from linebot.exceptions import (LineBotApiError, InvalidSignatureError)
import math


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('counter-table')
wheel_size = 22

# Line API利用に必要な変数設定
user_id = os.getenv('LINE_USER_ID', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
line_bot_api = LineBotApi(channel_access_token)

t_delta = dt.timedelta(hours=9)
JST = dt.timezone(t_delta, 'JST') 
now = dt.datetime.now(JST)
yesterday = now - dt.timedelta(1)

#--------------------
# 日時の桁揃えを行う関数
#--------------------

def digit_alignment(arg):
    if len(arg) == 1:
        arg = '0' + arg
    return arg

#--------------------
# 指定した日のカウントを返す関数
#--------------------

def get_count(date):
    
    try:
        response = table.query(
        KeyConditionExpression=Key('date').eq(date)
    )
    except Exception as e:
        message = '[Error]' + '\n' + 'Error.'
        push_message(message)
        raise e

    
    return response['Items']


#--------------------
# Lineに送信するメッセージを作成する関数
#--------------------

def create_message(date, time=None):
    
    counter = get_count(date)
    
    if time == None:
        sum_count = 0
        
        message = '{}/{}/{}\n\n'.format(date[:4], date[4:6], date[6:])
        for item in counter:
            message += '{}h : {}\n'.format(item['time'][:2], item['count'])
            sum_count += int(item['count'])
        
        dist = math.pi * int(wheel_size) * sum_count / 100
        
    else:
        try:
            message = '{}/{}/{}\n\n'.format(date[:4], date[4:6], date[6:])
            count = list(filter(lambda item: item['time'][:2] == time, counter))[0]['count']
            message += '{}h : {}\n'.format(time, count)
            dist = math.pi * int(wheel_size) * int(count) / 100
        except IndexError:
            message = '[Error]' + '\n' + 'No data found.'
            push_message(message)
            raise ValueError(message)  
    
    message += '\n{:.2f}m'.format(dist)
    
    return message


#--------------------
# Lineにメッセージを送信する関数
#--------------------

def push_message(message):
    messages = TextSendMessage(text=message)
    line_bot_api.push_message(user_id, messages=messages)

#--------------------
# Main
#--------------------

def lambda_handler(event, context):
    #print(json.dumps(event))

    if event["events"] == "Scheduled Event":
        date = yesterday.strftime('%Y%m%d')
        time = None
        
    else:
        # Lineに入力したテキストを変数に格納
        #args = json.loads(event['body'])['events'][0]['message']['text'].split(' ')
        args = event['events'][0]['message']['text'].split(' ')
        print(args)
        
        if "".join(args) in ['today', 'Today', '今日']:
            date = now.strftime('%Y%m%d')
            time = None
        elif len(args) == 2:
            try:
                args[0] = digit_alignment(args[0])
                args[1] = digit_alignment(args[1])
                check_date_format = now.strftime('%Y') + args[0] + args[1]
                dt.datetime.strptime(check_date_format, '%Y%m%d')
                date = now.strftime('%Y') + args[0] + args[1]
                time = None
            except ValueError:
                message = '[Error]' + '\n' + 'Incorrect data format, should be MM DD'
                push_message(message)
                raise ValueError(message)  
        elif len(args) == 3:
            if len(args[0]) == 4:
                try:
                    args[1] = digit_alignment(args[1])
                    args[2] = digit_alignment(args[2])
                    check_date_format = args[0] + args[1] + args[2]
                    dt.datetime.strptime(check_date_format, '%Y%m%d')
                    date = args[0] + args[1] + args[2]
                    time = None
                except ValueError:
                    message = '[Error]' + '\n' + 'Incorrect data format, should be YYYY MM DD'
                    push_message(message)
                    raise ValueError(message)  
            else:
                try:
                    args[0] = digit_alignment(args[0])
                    args[1] = digit_alignment(args[1])
                    args[2] = digit_alignment(args[2])
                    check_date_format = now.strftime('%Y') + args[0] + args[1] + args[2]
                    dt.datetime.strptime(check_date_format, '%Y%m%d%H')
                    date = now.strftime('%Y') + args[0] + args[1]
                    time = args[2]
                except ValueError:
                    message = '[Error]' + '\n' + 'Incorrect data format, should be MM DD HH'
                    push_message(message)
                    raise ValueError(message)  
        elif len(args) == 4:
            try:
                args[1] = digit_alignment(args[1])
                args[2] = digit_alignment(args[2])
                args[3] = digit_alignment(args[3])
                check_date_format = args[0] + args[1] + args[2] + args[3]
                dt.datetime.strptime(check_date_format, '%Y%m%d%H')
                date = args[0] + args[1] + args[2]
                time = args[3]
            except ValueError:
                message = '[Error]' + '\n' + 'Incorrect data format, should be YYYY MM DD HH'
                push_message(message)
                raise ValueError(message)  
        else:
            message = '[Error]' + '\n' + 'Incorrect data format, should be YYYY MM DD'
            push_message(message)
            raise ValueError(message)  
    
    
     # Line送信用メッセージの作成
    message = create_message(date, time)

    # Lineにメッセージ送信
    push_message(message)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }