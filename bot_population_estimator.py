import tweepy

from secrets import consumer_key, consumer_secret, access_token, access_token_secret


def get_api_instance():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, timeout=60)
    return api
