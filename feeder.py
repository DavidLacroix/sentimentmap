import tweepy
from tweepy import Stream
import random
import os
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pymongo.errors import PyMongoError
from pymongo import MongoClient
import datetime

class Feeder():
    def __init__(self, listener, twitter_consummer_key, twitter_consummer_secret, twitter_access_token, twitter_access_token_secret):
        self.auth = tweepy.OAuthHandler(twitter_consummer_key, twitter_consummer_secret)
        self.auth.set_access_token(twitter_access_token, twitter_access_token_secret)
        self.stream = Stream(self.auth, listener, timeout=30.0)
        
    def listen(self, bounding_box=[-180,-90,180,90]):
        print("Streaming tweets from within {} in language 'en'".format(bounding_box))
        self.stream.filter(locations=bounding_box, languages=["en"], async=False)

class FeedMongoListener(tweepy.StreamListener):
    def __init__(self, mongo_username, mongo_pwd, mongo_cluster, database_name, collection_name, api=None):
        tweepy.StreamListener.__init__(self, api=api)
        self.analyser = SentimentIntensityAnalyzer()
        
        self.mongo_client = MongoClient('mongodb+srv://{}:{}@{}'.format(mongo_username, mongo_pwd, mongo_cluster))
        self.mongo_db = self.mongo_client[database_name]
        self.mongo_collection = self.mongo_db[collection_name]
        
        self.tweet_parsed_count = 0
        self.tweet_success_count = 0
        
    def on_error(self, status_code):
        if status_code == 420:
            return False
    
    def analyse_sentiment(self, sentence):
        return self.analyser.polarity_scores(sentence)
    
    # Create a random location within the boundingbox 
    def estimate_location(self, bounding_box, keep_digits=6):
        lon = round(random.uniform(bounding_box[0][0], bounding_box[2][0]), keep_digits)
        lat = round(random.uniform(bounding_box[0][1], bounding_box[2][1]), keep_digits)
        return [lon, lat]
    
    def parse_status(self, status):
        dic = {}
        try:
            # Get the actual tweet content
            try:
                dic['text'] = status.extended_tweet["full_text"]
            except AttributeError:
                dic['text'] = status.text
            # Get the tweet id
            dic['id'] = status.id_str
            dic['country_code'] = status.place.country_code
            dic['created_at'] = datetime.datetime.fromtimestamp(int(status.timestamp_ms)/1000.0)
            # Has precise tweet location
            if status.geo:
                # coordinate as [lon, lat]
                dic['location'] = status.coordinates['coordinates']
                dic['coordinate_accuracy'] = 1
            # Parse poi
            elif status.place.place_type == 'poi':
                bb = status.place.bounding_box.coordinates[0]
                dic['location'] = bb[0]
                dic['coordinate_accuracy'] = 0.9
            # Parse city or neighbourhood bounding_box
            elif status.place.place_type == 'city':
                bb = status.place.bounding_box.coordinates[0]
                dic['location'] = self.estimate_location(bb)
                dic['coordinate_accuracy'] = 0.25
            elif status.place.place_type == 'neighborhood':
                bb = status.place.bounding_box.coordinates[0]
                dic['location'] = self.estimate_location(bb)
                dic['coordinate_accuracy'] = 0.50
            else:
                raise AttributeError("Could not geolocate the tweet")
        except Exception as e:
            print("Tossing tweet: {}".format(e))
            return None
        
        return dic
    
    def parse_sentiment(self, tweet_text):
        dic = {}
        try:
            sentiment = self.analyse_sentiment(tweet_text)
            if(sentiment['neu'] < 1):
                dic['sentiment_neg'] = sentiment['neg']
                dic['sentiment_neu'] = sentiment['neu']
                dic['sentiment_pos'] = sentiment['pos']
                #print("{} - {}".format(dic['sentiment_neu'], tweet_text))
            else:
                raise AttributeError("Sentiment is neutral only")
        except Exception as e:
            print("Tossing tweet: {}".format(e))
            return None 
        
        return dic
        
    def build_geojson(self, tweet_dic, sentiment_dic):
        return {
            'type': "Feature",
            'property': {
                'text': tweet_dic['text'],
                'id': tweet_dic['id'],
                'country_code': tweet_dic['country_code'],
                'created_at': tweet_dic['created_at'],
                'coordinate_accuracy': tweet_dic['coordinate_accuracy'],
                'sentiment_neg': sentiment_dic['sentiment_neg'],
                'sentiment_neu': sentiment_dic['sentiment_neu'],
                'sentiment_pos': sentiment_dic['sentiment_pos']
            },
            'geometry': {
                'type': "Point",
                'coordinates': tweet_dic['location']
            }    
        }
        
    def insert_to_mongo(self, geojson):
        try:
            result = self.mongo_collection.insert_one(geojson)
            self.tweet_success_count += 1
            return result
        except PyMongoError as e:
            print("Failed to insert {}: {}".format(geojson), e)
        
    def on_status(self, status):
        self.tweet_parsed_count += 1
        # return True skip that status but keeps the Stream running
        
        parsed_tweet = self.parse_status(status)
        if(parsed_tweet is None): return True
        
        parsed_sentiment = self.parse_sentiment(parsed_tweet['text'])
        if(parsed_sentiment is None): return True
        
        # Create geoJson from dictionnaries
        geojson = self.build_geojson(parsed_tweet, parsed_sentiment)
        
        result = self.insert_to_mongo(geojson)
        print("[{}/{}] Inserted new document under _id {}: {}".format(self.tweet_success_count, self.tweet_parsed_count, result.inserted_id, geojson))      
    
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
        