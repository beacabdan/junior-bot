class Bot:
    def __init__(self):
        self.description = "I'm a bot"

    def print_description(self):
        print(self.description)


class TwitterBot(Bot):
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        super().__init__()
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.description = "I'm a bot that can be used to publish tweets!"
