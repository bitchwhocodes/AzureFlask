from flask import request, url_for
from flask import Flask, jsonify
from flask.ext.api import FlaskAPI, status, exceptions
import sys
import tweepy
import json
import re
import time
import os

from bson import json_util

from pymongo import MongoClient




@classmethod
def parse(cls, api, raw):
   status = cls.first_parse(api, raw)
   setattr(status, 'json', json.dumps(raw))
   return status
tweepy.models.Status.first_parse = tweepy.models.Status.parse
tweepy.models.Status.parse = parse

CONSUMER_KEY = os.getenv('CONSUMER_KEY')#'Abbubgs42wD8dNzqFjl1luvbI'
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')#rAFYvH32fwVfsIukeTjATpLamqDkTlN641JarJo5pF9pkfH6MN'
ACCESS_KEY = os.getenv('ACCESS_KEY')#'2742224263-9G5QIFOfNA4IhXtY748XyK49PMCiq8xI0Z3MCz7'
ACCESS_SECRET = os.getenv('ACCESS_SECRET')#'HD5GhNdh55Su1tVp4bFgLZ3b3775ff8IMCRE0hgdIwBRR'

app = FlaskAPI(__name__)


@app.route("/user/<twittername>",methods=['GET'])
def latest_tweets(twittername):
	# get the lastest tweets by user name

	items = get_latest_tweets(twittername)
	if not items:
		items = get_tweets(twittername)
	return items

@app.route("/user/<twittername>/top/",methods=['GET'])
@app.route("/user/<twittername>/top/<limit>",methods=['GET'])
def get_top_retweets(username,limit=5):
	connection = MongoClient()
	collection = connection.tweeter.tweets
	hasTweets = collection.find({'user.screen_name':username})[0]
	if hasTweets.count():
		items = collection.find({'user.screen_name':username}).sort('retweet_count',pymongo.DESCENDING)[limit]
	
	else:
		get_latest_tweets(username)
		items = collection.find({'user.screen_name':username}).sort('retweet_count',pymongo.DESCENDING)[limit]

	connection.close()
	return items



def get_latest_tweets(username):
	connection = MongoClient()
	collection = connection.tweeter.tweets
	items = collection.find({'user.screen_name':username})

	json_docs = [json.dumps(doc, default=json_util.default) for doc in items]
	return json_docs
	

def get_tweets(username):
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	api = tweepy.API(auth)
	statuses = api.user_timeline(username,count=800)

	connection = MongoClient()
	db = connection.tweeter.tweets
	for status in statuses:
		db.save(json.loads(status.json))

	items = get_latest_tweets(username)
	return items


def replace_url_to_link(value):
    # Replace url to link
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    # Replace email to mailto
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value

if __name__ == "__main__":
    app.run(debug=True)