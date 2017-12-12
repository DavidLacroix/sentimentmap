# A simple sandbox project

[link to the demo](https://sentimentmap.herokuapp.com/)

## What you need to know
The VADER algorithm a rule-based algorithm that is both performant and light weight (no training data). For those advantages the algorithm is pretty effective and has been trained to work well on social media. This was done by using Amazon Mechanical Turk to label some dictionnaries and overall improve the quality of the training data set([more](http://comp.social.gatech.edu/papers/icwsm14.vader.hutto.pdf)).
I am purposely eliminating all tweet that are hard to geolocate but had to make some compromise to get enough data. I am working on UK and I am keeping tweets that are at least indicating the city they were sent from. When a tweet doesn't have a precise location I am using the boundingbox of the city to create a 'fake' location, that is to simulate a more realistic distribution of the data. I am also getting rid of tweets that are considered as "neutral" by the algorithm as they are of little interest to me in that exercise.

That is it! Have a look, play around, try to find some weird tendencies or just peek into what people have to say and where (hint: it was snowing in London when I started capturing the data).

## About the stack
One Python backend script to stream ([Tweepy](https://github.com/tweepy/tweepy)) and analyse ([VaderSentiment](https://github.com/cjhutto/vaderSentiment)) tweets from Twitter API.They are then stored in a mongo database ([Pymongo](https://api.mongodb.com/python/current/) and [Mongodb Atlas](https://www.mongodb.com/cloud/atlas/)). This is to provide enough data to do further analysis, data viz and hopefully practice machine learning.

A [Flask](http://flask.pocoo.org/) app deployed in [Heroku](https://www.heroku.com/) is used to compute and forward the data to [Leaflet](http://leafletjs.com/), [Plotly.js](https://plot.ly/javascript/) or any other nice lib in the future.
 
## About the project
The project is inspired by one coding challenge from master Siraj Raval [@sirajology](https://twitter.com/sirajology?lang=en) on his youtube data science and machine learning series. It has come to be a fun project so I am trying to push it a bit further.
