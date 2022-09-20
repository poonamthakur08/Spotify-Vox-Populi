from kafka import KafkaConsumer
from pymongo import MongoClient
from json import loads
import time
import json

consumer = KafkaConsumer(
    "analysis_tweets",
    bootstrap_servers=["localhost:9092"],
    auto_offset_reset="latest",
    enable_auto_commit=True,
)

import redis

r = redis.StrictRedis(host="localhost", port=6379, db=0)

for message in consumer:
    message = message.value.decode("utf-8")
    q = message.split("**%**")
    tmp = json.loads(q[0])
    query = tmp["query"]
    r.sadd(query, message)
