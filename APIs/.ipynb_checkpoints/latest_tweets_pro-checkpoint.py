from kafka import KafkaProducer
import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import requests
import time

access_token = ""
access_token_secret = ""
api_key = ""
api_secret = ""
bearer_token = ""


class StdOutListener(StreamListener):
    def on_data(self, data):
        json_ = json.loads(data)
        url = json_["id_str"]
        url = "https://twitter.com/x/status/" + url
        user_name = json_["user"]["name"]
        user_url = json_["user"]["screen_name"]
        user_pic = json_["user"]["profile_image_url"]
        full_text = json_["text"]

        if "extended_tweet" in json_.keys():
            full_text = json_["extended_tweet"]["full_text"]

        res = {
            "query": query,
            "url": url,
            "user_name": user_name,
            "user_id": user_url,
            "user_pic": user_pic,
            "text": full_text,
        }
        producer.send("last_tweets", value=res)
        return True

    def on_error(self, status):
        print(status)


producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    api_version=(0, 11, 5),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

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
    # myStream.filter(track=['python'], async=True)
    stream.filter(track=[new_query], is_async=True)
    return stream


def disconnect(new_query):
    global stream
    # stream.disconnect()
    global query
    query = new_query
    time.sleep(2)
