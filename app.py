from flask import Flask, render_template, request, jsonify
from pymongo.errors import PyMongoError
from pymongo import MongoClient
import os
import traceback
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
analyser = SentimentIntensityAnalyzer()

def fetch_tweets(collection, search="", accuracy=0, bounding_box={'SW': [0,0], 'NE': [0,0]}, result_limit=10000):
    search_data_query = {
        'properties.geometry_accuracy' : {'$gt' : accuracy},
        #'properties.text': {'$regex': search},
        '$text': {'$search': '"' + search + '"'},
        'geometry': {
           '$geoWithin': {
              '$box': [
                bounding_box['SW'],
                bounding_box['NE']
              ]
           }
        }
    }
    
    search_stats_query = [
        {'$match': search_data_query},
        {'$group':{
            '_id': "all", 
            'total':{'$sum': 1},
            'mean_pos': {'$avg': "$properties.pos"},
            'stddev_pos': { '$stdDevPop': "$properties.pos" },
            'mean_neg': {'$avg': "$properties.neg"},
            'stddev_neg': { '$stdDevPop': "$properties.neg" }
        }}
    ]
    
    global_stats_query = [
        {'$group':{
            '_id': "all", 
            'total':{'$sum': 1},
            'mean_pos': {'$avg': "$properties.pos"},
            'stddev_pos': { '$stdDevPop': "$properties.pos" },
            'mean_neg': {'$avg': "$properties.neg"},
            'stddev_neg': { '$stdDevPop': "$properties.neg" }
        }}
    ]
    
    response = {
        'meta': {
            'search': search,
            'search_sentiment':  analyser.polarity_scores(search),
            'accuracy': accuracy,
            'bounding_box': bounding_box,
            'search-stats': {}, 
            'global-stats': {}
        },
        'data': [], }

    # Get search data
    data_cursor = collection.find(search_data_query).limit(result_limit) #threeshold to avoid blowing up leaflet
    for record in data_cursor:
        record['_id'] = str(record['_id'])
        response['data'].append(record)
    # For the search data, get basic stats
    search_stats_cursor = collection.aggregate(search_stats_query)
    response['meta']['search-stats'] = next(search_stats_cursor, {})
    # For the whole dataset, get basic stats
    global_stats_cursor = collection.aggregate(global_stats_query)
    response['meta']['global-stats'] = next(global_stats_cursor, {})

    return response;

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tweet')
def tweet():
        search = str(request.args.get('search'))
        accuracy = float(request.args.get('accuracy'))
        bounding_box = {
            'SW': [float(request.args.get('SWlon')), float(request.args.get('SWlat'))],
            'NE': [float(request.args.get('NElon')), float(request.args.get('NElat'))]
        }
        
        with MongoClient('mongodb+srv://{}:{}@{}'.format(os.environ['SENTIMENT_APP_MONGO_USER'], os.environ['SENTIMENT_APP_MONGO_PWD'], os.environ['SENTIMENT_APP_MONGO_CLUSTER'])) as mongo_client:
            mongo_db = mongo_client['sentiment_db']
            mongo_collection = mongo_db['tweets']
            
            response = fetch_tweets(mongo_collection, search, accuracy, bounding_box)    
        
        return jsonify(response)
  

if __name__ == "__main__":
    app.run(debug=True)