import json
import random
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentTweetParser():
    def __init__(self):
        self.analyser = SentimentIntensityAnalyzer()
    
    def estimate_location(self, bounding_box, keep_digits=6):
        lon = round(random.uniform(bounding_box[0][0], bounding_box[2][0]), keep_digits)
        lat = round(random.uniform(bounding_box[0][1], bounding_box[2][1]), keep_digits)
        return [lon, lat]
    
    def analyse_sentiment(self, sentence):
        return SentimentIntensityAnalyzer().polarity_scores(sentence)
    
    def extract_location(self, tweet):
        # Coordinate as [lon, lat]
        location = {'coordinate': [], 'accuracy': 0}
        # Actual precise geolocation
        if tweet['geo']:
            location['coordinate'] = tweet['geo']['coordinates']
            location['accuracy'] = 1
        # Estimate from 'Place' feature
        else:
            bounding_box = tweet['place']['bounding_box']['coordinates'][0]
            if tweet['place']['place_type'] == 'poi':
                location['coordinate'] = bounding_box[0]
                location['accuracy'] = 0.9
            elif tweet['place']['place_type'] == 'neighborhood':
                location['coordinate'] = self.estimate_location(bounding_box)
                location['accuracy'] = 0.50
            elif tweet['place']['place_type'] == 'city':
                location['coordinate'] = self.estimate_location(bounding_box)
                location['accuracy'] = 0.25
            else:
                raise ValueError("Could not geolocate the tweet accurately")
        return location
    
    def parse(self, tweet):
        try:
            # Tweet is considered extended after 140char
            try:
                text = tweet['extended_tweet']['full_text']
            except KeyError:
                text = tweet['text']
            id = tweet['id_str']
            country_code = tweet['place']['country_code']
            created_at = datetime.datetime.fromtimestamp(int(tweet['timestamp_ms'])/1000.0)
            coordinate, coordinate_accuracy = self.extract_location(tweet)
            neg, neu, pos, compound = self.analyse_sentiment(text).values()
            if neu == 1: raise ValueError("Sentiment is neutral only")
        except ValueError as e:
            print("Tossing tweet: {}".format(e))
            return None
        
        return {
            'type': "Feature",
            'property': {
                'text': text,
                'id': id,
                'country_code': country_code,
                'created_at': created_at,
                'geometry_accuracy': coordinate_accuracy,
                'pos': pos,
                'neu': neu,
                'neg': neg,
                'compound': compound
            },
            'geometry': {
                'type': "Point",
                'coordinates': coordinate
            }    
        }