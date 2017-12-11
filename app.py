from flask import Flask, render_template, request, jsonify
from pymongo.errors import PyMongoError
from pymongo import MongoClient
import os
import traceback

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/tweet')
def tweet():
        SW = [float(request.args.get('SWlon')), float(request.args.get('SWlat'))]
        NE = [float(request.args.get('NElon')), float(request.args.get('NElat'))]
        search = str(request.args.get('search'))
        accuracy = float(request.args.get('accuracy'))
            
        mongo_client = MongoClient('mongodb+srv://{}:{}@{}'.format(os.environ['SENTIMENT_APP_MONGO_USER'], os.environ['SENTIMENT_APP_MONGO_PWD'], os.environ['SENTIMENT_APP_MONGO_CLUSTER']))
        mongo_db = mongo_client['sentiment_db']
        mongo_collection = mongo_db['tweets']
        
        query = {
            'properties.geometry_accuracy' : {'$gt' : accuracy},
            #'properties.text': {'$regex': search},
            '$text': {'$search': search},
            'geometry': {
               '$geoWithin': {
                  '$box': [
                    SW,
                    NE
                  ]
               }
            }
        }
        data = []
        
        cursor = mongo_collection.find(query)
        for record in cursor:
            record['_id'] = str(record['_id'])
            data.append(record)
            
        mongo_client.close()
        
        return jsonify(data)
  

if __name__ == "__main__":
    app.run(debug=True)