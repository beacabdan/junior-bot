import tweepy
import time


class Bot:
    def __init__(self):
        self._description = "I'm a bot"

    def print_description(self):
        print(self._description)


class TwitterBot(Bot):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        super().__init__()
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self._description = "I'm a bot that can be used to publish tweets!"
        self._waiting_time = 5 * 60
        self._attempts = 3

        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth)

    @property
    def waiting_time(self):
        return self._waiting_time

    @waiting_time.setter
    def waiting_time(self, minutes):
        self._waiting_time = minutes * 60

    @property
    def attempts(self):
        return self._attempts

    @attempts.setter
    def attempts(self, attempts):
        self._attempts = attempts

    # Handling the rate limit using cursors
    def limit_handled(self, cursor):
        attempts = 1
        while attempts <= self.attempts:
            try:
                yield next(cursor)
            except StopIteration:
                break
            except GeneratorExit:
                break
            except Exception:
                print("Pausando la ejecución", self.waiting_time // 60, "minutos (intento", str(attempts) + "/" + str(self.attempts) + ")")
                time.sleep(self.waiting_time)
                attempts += 1
        if attempts == self.attempts + 1:
            print("Ha pasado demasiado tiempo, me rindo :(")

    # Iterate through all of the authenticated user's print_friends
    def print_friends(self, num_items=10):
        for friend in self.limit_handled(tweepy.Cursor(self.api.friends).items(limit=num_items)):
            print(friend.screen_name, "("+str(friend.followers_count)+")")

    # Iterate through the first X statuses in the home timeline
    def timeline(self, num_items=10):
        lista = []
        for status in self.limit_handled(tweepy.Cursor(self.api.home_timeline, tweet_mode="extended").items(limit=num_items)):
            lista.append(status.full_text)
        return lista
