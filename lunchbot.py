import json
import requests
from flask import Flask
app = Flask(__name__)
from flask import request
from flask import jsonify
from flask_wtf import CSRFProtect
from datetime import datetime
import time
import sched
from pymongo import MongoClient
import os
import pandas as pd
from dotenv import load_dotenv, find_dotenv


#mongodb details
load_dotenv(find_dotenv(), override = True)
mongodb_url = os.environ.get("mongodb_url")
client = MongoClient(mongodb_url)
db = client['kitchen_bot']
collection = db['food']
posts = db.posts
now = datetime.now()

# print(mongodb_url)

"""
curl -i -X POST --data-urlencode 'payload={"channel":"testchannel","userne": "lunch-bot",
"icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
"text": "# Hello, your lunch is ready\n_Come up if you want fresh food._ :shallow_pan_of_food:"}
' http://10.10.10.151:12000/hooks/nddd74m4b3ynjqtew84a6c54gr
"""
csrf = CSRFProtect(app)
yessnack = 0
nosnack = 0
yeslunch = 0
nolunch = 0
user_list = {'user_id':[],'snack_response':[], 'lunch_response':[] }

@app.route("/getmessage",methods=["POST"])
@csrf.exempt
def hello_world():
  global yessnack
  global nosnack
  global yeslunch
  global nolunch
  global user_list

  r = request.data
  req = json.loads(r.decode())
  action = req['context']['action']
  userid = req['user_id']
  print(req)
  print(userid)


  if (userid not in list(user_list.values())[list(user_list.keys()).index('user_id')]):
    user_list['user_id'].append(userid)
    if action == 'yesSnack':
      yessnack += 1
      user_list['snack_response'].append(action)
      value = user_list['snack_response'][user_list['user_id'].index(userid)]
      sendupdatesnack(value)
      mongo_post_snack(userid)

    if action == 'noSnack':
      nosnack += 1
      user_list['snack_response'].append(action)
      value = user_list['snack_response'][user_list['user_id'].index(userid)]
      sendupdatesnack(value)
      mongo_post_snack(userid)

    if action == 'yeslunch':
      yeslunch += 1
      user_list['lunch_response'].append(action)
      value = user_list['lunch_response'][user_list['user_id'].index(userid)]
      sendupdatelunch(value)
      mongo_post_lunch(userid)

    if action == 'nolunch':
      nolunch += 1
      user_list['lunch_response'].append(action)
      value = user_list['lunch_response'][user_list['user_id'].index(userid)]
      sendupdatelunch(value)
      mongo_post_lunch(userid)
  
  else:
    print(user_list, "\n", action)
    if action == user_list['lunch_response'][user_list['user_id'].index(userid)]:
      message= "you enter it twice"

    elif action == 'yesSnack':
      yessnack += 1
      nosnack -=1
      user_list['snack_response'][user_list['user_id'].index(userid)] = action 
      update = user_list['snack_response'][user_list['user_id'].index(userid)]
      sendupdatesnack(update)
      mongo_post_snack(userid)

    elif action == 'noSnack':
      yessnack -=1
      nosnack +=1
      user_list['snack_response'][user_list['user_id'].index(userid)] = action
      update = user_list['snack_response'][user_list['user_id'].index(userid)]
      sendupdatesnack(update)
      mongo_post_snack(userid)

    elif action == 'yeslunch':
      yeslunch += 1 
      nolunch -=1 
      user_list['lunch_response'][user_list['user_id'].index(userid)] = action
      update = user_list['lunch_response'][user_list['user_id'].index(userid)]
      sendupdatelunch(update)
      mongo_post_lunch(userid)
    
    elif action == 'nolunch':
      yeslunch -=1
      nolunch +=1
      user_list['lunch_response'][user_list['user_id'].index(userid)] = action
      update = user_list['lunch_response'][user_list['user_id'].index(userid)]
      sendupdatelunch(update)
      mongo_post_lunch(userid)

  data = {'statusCode':200, 'headers':{'Content-Type':'application/json'},'body':json.dumps({'message':'you did good, or sucks!!'})}
  return jsonify(data)
  # return {
  #       'statusCode': '200',
  #       'headers': {
  #           'Content-Type': 'application/json',
  #       },
  #       'body': json.dumps({
  #           'ephemeral_text': 'Your vote has been updated.'
  #       }),
  #   }

# personal access token of Kitchen bot : 6y6pz38n83gn7bhadkf6egqxgw
def sendupdatesnack(value):
  global yessnack
  global nosnack
  global user_list
  payload = {
    "channel": "testchannel",
    "username": "lunch-bot",
    "type": "ephemeral",
    "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
    "text" : "# Your answer is updated as {} \n Total yes : {} \t\t\t Total no : {} \n {}".format(value, yessnack, nosnack, user_list)
  } 
  url = 'http://10.10.30.133:8065/hooks/4ahifytfdbn85kjwe9hzat1qdh'
  headers = {'content-type': 'application/json'}
  r = requests.post(url, data = json.dumps(payload) , headers = headers) 

def sendupdatelunch(value):
  global yeslunch
  global nolunch
  payload = {
    "channel": "testchannel",
    "username": "lunch-bot",
    "type": "ephemeral",
    "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
    "text" : "# Your answer is updated as {} \n Total yes : {} \t\t\t Total no : {} \n {}".format(value, yeslunch, nolunch, user_list)
  } 
  url = 'http://10.10.30.133:8065/hooks/4ahifytfdbn85kjwe9hzat1qdh'
  headers = {'content-type': 'application/json'}
  r = requests.post(url, data = json.dumps(payload) , headers = headers) 

def mongo_post_snack(userid):
  global user_list
  date_ = datetime.now().replace(microsecond=0)
  if (len(user_list['snack_response']) >= user_list['user_id'].index(userid) >= 0) :
    #print(len(user_list['snack_response']), user_list['user_id'].index(userid))
    snack_response = user_list['snack_response'][user_list['user_id'].index(userid)]
  else:
    snack_response = ''
  if (len(user_list['lunch_response']) >= user_list['user_id'].index(userid) > 0):
    lunch_response = user_list['lunch_response'][user_list['user_id'].index(userid)]
  else:
    lunch_response = ''
  print(type(date_), type(userid), type(snack_response), type(lunch_response))
  post = {"date_time": date_,
          "user_id": userid,
          "snack_response": snack_response,
          "lunch_response": lunch_response,
          }
  print(user_list['user_id'].index(userid))
  posts.insert_one(post)

def mongo_post_lunch(userid):
  global user_list
  date_ = datetime.now().replace(microsecond=0)
  if (len(user_list['lunch_response']) >= user_list['user_id'].index(userid) >= 0):
    lunch_response = user_list['lunch_response'][user_list['user_id'].index(userid)]
  else:
    lunch_response = ''
  if (len(user_list['snack_response']) >= user_list['user_id'].index(userid) > 0) :
    #print(len(user_list['snack_response']), user_list['user_id'].index(userid))
    snack_response = user_list['snack_response'][user_list['user_id'].index(userid)]
  else:
    snack_response = ''
  print(type(date_), type(userid), type(snack_response), type(lunch_response))
  post = {"date_time": date_,
          "user_id": userid,
          "snack_response": snack_response,
          "lunch_response": lunch_response,
          }
  print(user_list['user_id'].index(userid))
  posts.insert_one(post)

def sendlunch():
  payload = {
          "channel": "testchannel",
          "username": "lunch-bot",
          "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
          "attachments": [{
            "pretext": "---- Kindly answer this ----",
            "text": "Do you want to eat lunch :shallow_pan_of_food:",
            "actions": [{
              "name": "Yes :ballot_box_with_check:",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "yeslunch"
                }
              }
            }, {
              "name": "No :x:",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "nolunch"
                }
              }
            }]
          }],
          "update": {
            "props": {
              "response_type": "in_channel",
              "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
              "attachments": [{
                "message": "this is message"
              }]
            }

          }
        }
  url = 'http://10.10.30.133:8065/hooks/4ahifytfdbn85kjwe9hzat1qdh'
  headers = {'content-type': 'application/json'}
  r = requests.post(url, data = json.dumps(payload) , headers = headers) 
  print (r.text)

def sendlunchuser():
  payload = {
          "channel": "@sushant",
          "username": "lunch-bot",
          "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
          "attachments": [{
            "pretext": "---- Kindly answer this ----",
            "text": "Do you want to eat lunch :shallow_pan_of_food:",
            "actions": [{
              "name": "Yes :ballot_box_with_check:",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "yeslunch"
                }
              }
            }, {
              "name": "No :x:",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "nolunch"
                }
              }
            },
            {"No :x:": {
              "message":"updated!"
            },
              "ephemeral_text": "you updated THE POST"
            }
            ]

          }]
          # "update": {
          #   "props": {
          #     "response_type": "in_channel",
          #     "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
          #     "attachments": [{
          #       "message": "this is message"
          #     }]
          #   }

          # }
        }
  url = 'http://10.10.30.133:8065/hooks/4ahifytfdbn85kjwe9hzat1qdh'
  headers = {'content-type': 'application/json'}
  r = requests.post(url, data = json.dumps(payload) , headers = headers) 
  print (r.text)


def sendsnack():
  payload = {
          "channel": "testchannel",
          "username": "lunch-bot",
          "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
          "attachments": [{
            "pretext": "---- Kindly answer this ----",
            "text": " Do you want to eat snack_ :shallow_pan_of_food:",
            "actions": [{
              "name": "Yes ",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "yesSnack"
                }
              }
            }, {
              "name": "No :x:",
              "integration": {
                "url": "http://10.10.30.133:5000/getmessage",
                "context": {
                  "action": "noSnack"
                }
              }
            }]
          }],
          "update": {
            "props": {
              "response_type": "in_channel",
              "icon_url": "https://images.g2crowd.com/uploads/product/image/large_detail/large_detail_1508920769/chatbotsbuilder.png",
              "attachments": [{
                "message": "this is message :x:"
              }]
            }

          }
        }
  url = 'http://10.10.30.133:8065/hooks/4ahifytfdbn85kjwe9hzat1qdh'
  headers = {'content-type': 'application/json'}
  r = requests.post(url, data = json.dumps(payload) , headers = headers) 
  print (r.text)

def jobs():
  print("jobs is being called")
  scheduler = sched.scheduler(time.time, time.sleep)
  
  now = time.time()
  x = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
  lunchtime = datetime.strptime(x.split(' ')[0] + ' 15:33:00','%Y-%m-%d %H:%M:%S')
  snacktime = datetime.strptime(x.split(' ')[0] + ' 15:32:30','%Y-%m-%d %H:%M:%S')

  scheduler.enterabs(lunchtime.timestamp(),2, sendlunch)
  scheduler.enterabs(snacktime.timestamp(),1, sendsnack)
  scheduler.run()

if __name__ == '__main__':
  sendlunch()
  #jobs()
  app.run(host='10.10.30.133', port=5000)