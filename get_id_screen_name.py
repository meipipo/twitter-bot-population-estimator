import sys
import tweepy

from secrets import consumer_key, consumer_secret, access_token, access_token_secret


def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, timeout=60)

    user_name = sys.argv[1]
    print("user id:", api.get_user(user_name).id)
    print("screen name:", api.get_user(user_name).screen_name)


if __name__ == "__main__":
    main()
