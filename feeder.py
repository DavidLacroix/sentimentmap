import tweepy
from tweepy import Stream
import random
import os
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pymongo.errors import PyMongoError
from pymongo import MongoClient
import datetime
from tweetparser import SentimentTweetParser

class FeedMongoListener(tweepy.StreamListener):
    def __init__(self, mongo_username, mongo_pwd, mongo_cluster, database_name, collection_name, api=None):
        tweepy.StreamListener.__init__(self, api=api)
        self.parser = SentimentTweetParser()
        
        self.mongo_client = MongoClient('mongodb+srv://{}:{}@{}'.format(mongo_username, mongo_pwd, mongo_cluster))
        self.mongo_db = self.mongo_client[database_name]
        self.mongo_collection = self.mongo_db[collection_name]
        
        self.tweet_parsed_count = 0
        self.tweet_success_count = 0
                
    def on_error(self, status_code):
        if status_code == 420:
            return False
        
    def insert_to_mongo(self, geojson):
        try:
            result = self.mongo_collection.insert_one(geojson)
            self.tweet_success_count += 1
            return result
        except PyMongoError as e:
            print("Failed to insert {}: {}".format(geojson), e)
        
    def on_status(self, status):
        self.tweet_parsed_count += 1
        
        geojson = self.parser.parse(status._json)
        if(geojson is None): return True
        
        result = self.insert_to_mongo(geojson)
        print("[{}/{}] Inserted new document under _id {}: {}".format(self.tweet_success_count, self.tweet_parsed_count, result.inserted_id, geojson))      
    
class Feeder():
    def __init__(self, listener, twitter_consummer_key, twitter_consummer_secret, twitter_access_token, twitter_access_token_secret):
        self.auth = tweepy.OAuthHandler(twitter_consummer_key, twitter_consummer_secret)
        self.auth.set_access_token(twitter_access_token, twitter_access_token_secret)
        self.stream = Stream(self.auth, listener, timeout=30.0)
        
    def listen(self, bounding_box=[-180,-90,180,90]):
        print("Streaming tweets from within {} in language 'en'".format(bounding_box))
        self.stream.filter(locations=bounding_box, languages=["en"], async=False)
    

if __name__ == '__main__':
    l = FeedMongoListener(os.environ['SENTIMENT_APP_MONGO_USER'],
                          os.environ['SENTIMENT_APP_MONGO_PWD'],
                          os.environ['SENTIMENT_APP_MONGO_CLUSTER'],
                          'sentiment_db',
                          'tweets')
    f = Feeder(l, 
               os.environ['SENTIMENT_APP_TWITTER_CONSUMMER_KEY'], 
               os.environ['SENTIMENT_APP_TWITTER_CONSUMMER_SECRET'], 
               os.environ['SENTIMENT_APP_TWITTER_ACCESS_TOKEN'], 
               os.environ['SENTIMENT_APP_TWITTER_ACCESS_TOKEN_SECRET'])
    f.listen([-12.62, 49.78, 1.93, 58.15])
        