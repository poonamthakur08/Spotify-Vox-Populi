import requests
import os
import json

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
BEARER_TOKEN = ""
bearer_token = BEARER_TOKEN

#from kafka import KafkaProducer
#producer = KafkaProducer(bootstrap_servers='localhost:9092') #Same port as your Kafka server
#topic_name = "number-tweets"

search_url = "https://api.twitter.com/2/tweets/counts/recent"
# Optional params: start_time,end_time,since_id,until_id,next_token,granularity


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentTweetCountsPython"
    return r


def connect_to_endpoint(url, params):
    response = requests.request("GET", search_url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def count_tweets(query):
    query_params = {'query': query,'granularity': 'day', 'search_count.fields': 'tweet_count'}
    json_response = connect_to_endpoint(search_url, query_params)
    data = json_response["data"]
    res = []
    date = []
    for i in range(len(data)):
        date.append(data[i]["start"][:10])
        res.append(data[i]["tweet_count"])
    res = {"Date" : date, "Count":res}
    return res
