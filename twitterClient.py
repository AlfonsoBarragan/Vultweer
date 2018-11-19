#!/usr/bin/python
# -*- coding: utf-8; mode: python -*-

from flask import Flask, request, redirect, url_for, flash, render_template, make_response, jsonify
from flask_oauthlib.client import OAuth

import requests

app = Flask(__name__)
app.config['DEBUG'] = True
oauth = OAuth()
mySession=None
currentUser=None

app.secret_key = 'development'


twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='YOUR_CONSUMER_KEY',
    consumer_secret='YOUR_CONSUMER_SECRET'
)

# Obtener token para esta sesion
@twitter.tokengetter
def get_twitter_token(token=None):
    global mySession

    if mySession is not None:
        return mySession['oauth_token'], mySession['oauth_token_secret']

# Limpiar sesion anterior e incluir la nueva sesion
@app.before_request
def before_request():
    global mySession
    global currentUser

    currentUser = None
    if mySession is not None:
        currentUser = mySession

# Pagina principal
@app.route('/')
def index():
    global currentUser

    tweets = []
    if currentUser is not None:
        resp = twitter.get(twitter.base_url+'/statuses/user_timeline.json')
        if resp.status == 200:
            tweets = resp.data
        else:
            flash('Impossible to access twitter...', "error")
    return render_template('index.html', user=currentUser, tweets=tweets)

@app.route('/operations', methods=['GET'])
def show_operations():
    if currentUser == None:
        return redirect(url_for('login'))

    return render_template('tweets_adm.html', user=currentUser, tweets=tweets)
@app.route('/valley', methods=['GET'])
def valley():
    global currentUser

    tweets = []
    if currentUser is not None:
        resp = twitter.get(twitter.base_url+'/statuses/home_timeline.json')
        if resp.status == 200:
            tweets = resp.data
        else:
            flash('Impossible to access twitter...', "error")
    return render_template('timeline.html', user=currentUser, tweets=tweets)

# Get auth token (request)
@app.route('/login')
def login():
    callback_url=url_for('oauthorized', next=request.args.get('next'))
    flash(u'You login succesfully!')
    return twitter.authorize(callback=callback_url or request.referrer or None)

# Eliminar sesion
@app.route('/logout')
def logout():
    global mySession

    mySession = None
    return redirect(url_for('index'))

# Callback
@app.route('/oauthorized', methods=['GET'])
def oauthorized():
    global mySession

    resp = twitter.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.', 'error')
    else:
        mySession = resp
    return redirect(url_for('index'))

# Operaciones
@app.route('/timeline')
def show_timeline():
    url_request = twitter.base_url
    resp        = twitter.get(url_request+"/statuses/home_timeline.json")

    return make_response(jsonify({"all":resp.data}), 200)

@app.route('/tweets')
def tweets():
    if currentUser == None:
        return redirect(url_for('login'))

    url_request = twitter.base_url
    resp        = twitter.get(url_request+"/statuses/user_timeline.json")

    return make_response(jsonify({"all":resp.data}), 200)

@app.route('/deleteTweet', methods=['POST'])
def deleteTweet():
    id_tweet        = request.form['idTweetDelete']
    destroy_tweet   = "{}.json".format(id_tweet)

    request_url = twitter.base_url
    resp        = twitter.post('{0}/statuses/destroy/{1}'.format(request_url, destroy_tweet))

    if resp.status == 200:
        flash(u'Tweet deleted!', "message")
    else:
        error = u'[ERROR {}] Sorry, and try again later...'.format(resp.status)
        flash(error, "error")

    return redirect(url_for('index'))

@app.route('/retweet', methods=['POST'])
def retweet():
    id_tweet        = request.form['idRepostTweet']
    repost_tweet    = "{}.json".format(id_tweet)

    request_url = twitter.base_url
    resp        = twitter.post('{0}/statuses/retweet/{1}'.format(request_url, repost_tweet))
    
    if resp.status == 200:
        flash(u'Tweet repost!')
    else:
        error = u'[ERROR {}] Sorry, and try again later...'.format(resp.status)
        flash(error, 'error')

    return redirect(url_for('index'))

@app.route('/follow', methods=['POST'])
def follow():
    id_user = request.form['idUser']
    
    if id_user == "":
        id_name               = request.form['idName']
        friendship_parameters = "create.json?screen_name={}&follow=true".format(id_name)
    else:
        friendship_parameters = "create.json?user_id={}&follow=true".format(id_user)

    request_url = twitter.base_url
    resp        = twitter.post('{0}/friendships/{1}'.format(request_url, friendship_parameters))

    if resp.status == 200:
        flash(u'You follow @{} {} succesfully!'.format(id_name, id_user))
    else:
        error = u'[ERROR {}] Sorry, and try again later...'.format(resp.status)
        flash(error, 'error')

    return redirect(url_for('index'))

@app.route('/find', methods=['POST'])
def find():

    searching_tokens = request.form['findTweet']
    if searching_tokens == "":
        error = u'[ERROR 0] Sorry, empty query...'
        flash(error, 'error')
    else:
        search_parameters   = 'tweets.json?q=%22{}%22'.format(searching_tokens.replace(" ","+"))
        request_url         = twitter.base_url
        resp                = twitter.get('{0}/search/{1}'.format(request_url, search_parameters))

        if resp.status == 200:
            flash(u'You find this tweets!')
            tweets  = resp.data
        else:
            error   = u'[ERROR {}] Sorry, and try again later...'.format(resp.status)
            flash(error, 'error')

        return render_template('tweets_finded.html', user=currentUser, tweets=tweets['statuses'])
    return redirect(url_for('index'))

@app.route('/tweet', methods=['POST'])
def tweet():
    if currentUser == None:
        redirect(url_for("login"))

    text = request.form['tweetText']

    request_url = twitter.base_url
    json_tweet  = {'status':text}
    resp        = twitter.post(request_url+'/statuses/update.json', data=json_tweet)

    if resp.status == 200:
        flash(u'Tweet send!')
    else:
        error = u'[ERROR {}] Sorry, and try again later...'.format(resp.status)
        flash(error, 'error')

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
