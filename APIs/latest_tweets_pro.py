from kafka import KafkaProducer
import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import requests
import time


access_token = "607625991-WFcqaqdDxALYRokUSS6JVHqeCBZb3GfbmSS3FpGz"
access_token_secret =  "D1uQfOcP21lQKmP0vsFxlf8GoFHqTfQYAvZE0Bja4IPnY"
api_key =  "KeSG46RbWBtNgxJI1kNB7lSu7"
api_secret =  "ING79wSpqKcg4xcrj1VQTITsUa9uPNu1fQWYk2EWoA7HtZXkmG"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAGBVbQEAAAAArX1fVXwiGZjpEccQB7ISyiBoDY4%3Db9FCiy3BC4dZFoHOvfUn5WzkMpcrwVjJlG3AN5RNhrbIxXSR2z"

headers = {"Authorization": "Bearer {}".format(bearer_token)}

query = "Drake"


class StdOutListener(StreamListener):
    def on_data(self, data):
        json_ = json.loads(data) 
        url = json_['id_str']
        url = 'https://twitter.com/x/status/'+url
        
        #url = 'https://publish.twitter.com/oembed?url='+url
        
        user_name = json_['user']['name']
        user_url = json_['user']['screen_name']
        user_pic = json_['user']['profile_image_url']
        full_text = json_['text']
        
        if 'extended_tweet' in json_.keys():
            full_text = json_['extended_tweet']['full_text']
        #response = requests.request("GET", url, headers = headers)
        
       # if response.status_code == 200:
       #     response = response.json()
       # else:
       #     return False
        res = {"query" : query,
                "url" : url,
                "user_name": user_name,
                "user_id": user_url,
                "user_pic": user_pic,
                "text" : full_text
              }
        producer.send("last_tweets", value = res)
        return True
    def on_error(self, status):
        print (status)



producer = KafkaProducer(bootstrap_servers='localhost:9092',  api_version=(0,11,5), value_serializer=lambda v: json.dumps(v).encode('utf-8'))

l = StdOutListener()
auth = OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)
stream = Stream(auth, l)

def produce_tweets(new_query):
    global stream
    global query 
    query = new_query
    stream.disconnect()
    time.sleep(2)    
    l = StdOutListener()
    stream = Stream(auth, l)
    #myStream.filter(track=['python'], async=True)
    stream.filter(track=[new_query], is_async=True)
    return stream
 
def disconnect(new_query):
    global stream
    #stream.disconnect()
    global query 
    query = new_query
    time.sleep(2)
    

