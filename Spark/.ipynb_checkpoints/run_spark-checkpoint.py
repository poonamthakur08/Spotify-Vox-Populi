from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import functions as F
from textblob import TextBlob
import json


def preprocessing(lines):
    words = lines.select(explode(split(lines.value, "t_end")).alias("value"))
    words = words.withColumn(
        "word", from_json(col("value"), MapType(StringType(), StringType()))
    )
    words = words.withColumn("word", to_json(col("word")))
    words = words.withColumn("word", json_tuple(words.word, "text"))
    words = words.na.replace("", None)
    words = words.na.drop()
    words = words.withColumn("word", F.regexp_replace("word", r"http\S+", ""))
    words = words.withColumn("word", F.regexp_replace("word", "@\w+", ""))
    words = words.withColumn("word", F.regexp_replace("word", "#", ""))
    words = words.withColumn("word", F.regexp_replace("word", "RT", ""))
    words = words.withColumn("word", F.regexp_replace("word", ":", ""))
    return words


# text classification
def polarity_detection(text):
    return TextBlob(text).sentiment.polarity


def subjectivity_detection(text):
    return TextBlob(text).sentiment.subjectivity


def text_classification(words):
    # polarity detection
    polarity_detection_udf = udf(polarity_detection, StringType())
    words = words.withColumn("polarity", polarity_detection_udf("word"))
    # subjectivity detection
    subjectivity_detection_udf = udf(subjectivity_detection, StringType())
    words = words.withColumn("subjectivity", subjectivity_detection_udf("word"))
    words = words.select(
        concat_ws("**%**", words.value, words.polarity, words.subjectivity).alias(
            "value"
        )
    )
    return words


import pyspark


sc = SparkSession.builder.appName("APP").getOrCreate()

df = (
    sc.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "last_tweets")
    .load()
)

words = preprocessing(df)
words = text_classification(words)
words = words.repartition(1)
words.writeStream.format("kafka").option(
    "kafka.bootstrap.servers", "localhost:9092"
).option("topic", "analysis_tweets").option(
    "checkpointLocation", "/datadrive/spark/tmp"
).start().awaitTermination()
