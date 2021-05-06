import tweepy
import time
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
import gspread
import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
import tensorflow as tf
import tensorflow_hub as hub
import matplotlib.pyplot as plt
import tempfile
from six.moves.urllib.request import urlopen
from six import BytesIO
from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
import os
from mxnet import npx
from mxnet import np as np1
from d2l import mxnet as d2l


class Bot:
    def __init__(self):
        self._description = "I'm a bot"

    def print_description(self):
        print(self._description)


class MusicBot(Bot):
    sp = None
    genius = None

    def __init__(self, client_id, client_secret):
        self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
        self.genius = Genius(access_token="")

    def get_image_of_artist(self, name):
        results = self.sp.search(q='artist:' + name, type='artist')
        items = results['artists']['items']
        if len(items) > 0:
            artist = items[0]
            print(artist['name'], artist['images'][0]['url'])

    def get_my_playlists(self):
        playlists = self.sp.user_playlists('beasays')
        return playlists['items']

    def get_playlists_by_cathegories(self):
        playlists = {}
        for cat in self.sp.categories()["categories"]["items"]:
            try:
                playlists[cat["name"]] = self.sp.category_playlists(cat["id"])["playlists"]["items"][0]["id"]
            except:
                pass

    def get_sentences_from_lyrics(self, lyrics):
        status = []
        song_lyrics = re.compile('\n\n|\[.*\]').sub('SPLIT', lyrics)
        song_lyrics = song_lyrics.replace('SPLITSPLIT', 'SPLIT').split('SPLIT')
        for part in song_lyrics:
            sentence = ""
            part = part.split("\n")
            if len(part) <= 4:
                for p in part:
                    sentence += p + " "
                if len(sentence) > 15:
                    sentence.replace("  ", " ")
                    sentence = sentence if sentence[:1] != "/ " else sentence[1:]
                    sentence = sentence if sentence[-1:] != " /" else sentence[:-1]
                    if sentence not in status and "vocal" not in sentence.lower() and "instrumental" not in sentence.lower() and "alan" not in sentence.lower() and "version" not in sentence.lower():
                        status.append(sentence)

        song_lyrics = lyrics.replace("\n\n", "\n").split("\n")
        for i in range(len(song_lyrics) - 1):
            if song_lyrics[i][0] == "[" or song_lyrics[i + 1][0] == "[":
                continue
            if song_lyrics[i][-2:] == song_lyrics[i + 1][-2:] and song_lyrics[i] != song_lyrics[i + 1]:
                sentence = song_lyrics[i] + " " + song_lyrics[i + 1]
                if sentence not in status:
                    status.append(sentence)
        return status

    def get_lyrics_of_song(self, name, artist):
        songs = self.genius.search_songs(name + " " + artist)
        try:
            it = 0
            while artist.lower() not in songs['hits'][it]['result']['primary_artist']['name'].lower() or name.lower() not in songs['hits'][it]['result']['full_title'].lower():
                it += 1
            url = songs['hits'][it]['result']['url']
            song_lyrics = self.genius.lyrics(song_url=url)
            return [self.get_sentences_from_lyrics(song_lyrics), url]
        except:
            return None

    def get_lyrics_of_playlist_random_song(self, playlists):
        statuses = []
        for pl in self.get_my_playlists():
            if pl["name"] not in playlists:
                continue
            for song in self.sp.playlist_items(pl["id"], limit=3, offset=random.randint(0, pl["tracks"]["total"] - 2))["items"]:
                artist = song["track"]["artists"][0]["name"]
                title = song["track"]["name"]
                url = song["track"]["external_urls"]["spotify"]
                status = self.get_lyrics_of_song(title, artist)
                if status:
                    status = status[0]
                    for s in status:
                        statuses.append(utils.to_sentence_case(s) + " -" + title + ", " + artist + " " + url)
        random.shuffle(statuses)
        for s in statuses:
            if 40 < len(s) < 270:
                return s
        return self.get_lyrics_of_playlist_random_song(playlists)

    def status_from_artist(self, artist):
        artist_id = self.sp.search(q='artist:' + artist, limit=1, type='artist')["artists"]["items"][0]["id"]
        top_tracks = self.sp.artist_top_tracks(artist_id)
        statuses = []
        for song in top_tracks["tracks"]:
            title = song["name"]
            url = song["external_urls"]["spotify"]  # .replace("https://", "")
            status = self.get_lyrics_of_song(title, artist)
            if status:
                status = status[0]
                for s in status:
                    statuses.append(utils.to_sentence_case(s) + " -" + title + ", " + artist + " " + url)

        random.shuffle(statuses)
        for s in statuses:
            if 40 < len(s) < 270:
                return s
        return self.status_from_artist(artist)


class TwitterBot(Bot):
    def __init__(self, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None):
        super().__init__()
        if consumer_key and consumer_secret and access_token and access_token_secret:
            self.consumer_key = consumer_key
            self.consumer_secret = consumer_secret
            self.access_token = access_token
            self.access_token_secret = access_token_secret
            auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            self.api = tweepy.API(auth)
        self._description = "I'm a bot that can be used to publish tweets!"
        self._waiting_time = 5 * 60
        self._attempts = 3
        self._fllwr = 1323581952767778816
        self._fllwd = 1323582040319660033
        self._trstd = 1323648206236979201
        self.desired_words = "data/desired_words.txt"
        self.undesired_words = "data/undesired_words.txt"
        print("(TWITTERBOT) Conectado a Twitter.")

    @property
    def desired_words(self):
        return self.__desired_words

    @desired_words.setter
    def desired_words(self, dw):
        try:
            f = open(dw, encoding='utf-8')
            self.__desired_words = [line.replace("\n", "") for line in f.readlines()]
            f.close()
        except:
            self._desired_words = []

    @property
    def undesired_words(self):
        return self.__undesired_words

    @undesired_words.setter
    def undesired_words(self, udw):
        try:
            f = open(udw, encoding='utf-8')
            self.__undesired_words = [line.replace("\n", "") for line in f.readlines()]
            f.close()
        except:
            self._undesired_words = []

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
                print("(TWITTERBOT) Pausando la ejecución", self.waiting_time // 60, "minutos (intento", str(attempts) + "/" + str(self.attempts) + ")")
                time.sleep(self.waiting_time)
                attempts += 1
        if attempts == self.attempts + 1:
            print("(TWITTERBOT) Ha pasado demasiado tiempo, me rindo :(")

    @staticmethod
    def getStatusText(status):
        if hasattr(status, "retweeted_status"):
            try:
                return status.retweeted_status.extended_tweet["full_text"]
            except AttributeError:
                return status.retweeted_status.full_text
        else:
            try:
                return status.extended_tweet["full_text"]
            except AttributeError:
                return status.full_text

    # def getStatusById(self, id):
    #     for status in self.limit_handled(tweepy.Cursor(self.api.statuses_lookup).items(limit=1)):

    # Iterate through all of the authenticated user's print_friends
    def print_friends(self, num_items=10):
        for friend in self.limit_handled(tweepy.Cursor(self.api.friends).items(limit=num_items)):
            print(friend.screen_name, "(" + str(friend.followers_count) + ")")

    # Iterate through the first X statuses in the home timeline
    def timeline(self, num_items=10):
        lista = []
        for status in self.limit_handled(tweepy.Cursor(self.api.home_timeline, tweet_mode="extended").items(limit=num_items)):
            lista.append(status)
        return lista

    @staticmethod
    def has_media(status):
        try:
            if len(status.entities["media"]) > 0:
                return True
        except:
            pass
        return False

    def analiza_estados(self, tuits, propiedades):
        analisis = [[] for _ in range(len(tuits))]
        for r in range(len(tuits)):
            for c in range(len(propiedades)):
                action = propiedades[c]
                if action == "texto":
                    content = self.getStatusText(tuits[r])
                elif action == "longitud":
                    content = len(self.getStatusText(tuits[r]))
                elif action == "lineas":
                    content = self.getStatusText(tuits[r]).count("\n") + 1
                elif action == "id":
                    content = tuits[r].id_str
                elif action == "likes":
                    content = tuits[r].favorite_count
                elif action == "autor":
                    content = tuits[r].user.name
                elif action == "fecha":
                    content = tuits[r].created_at.strftime("%m/%d/%Y, %H:%M:%S")
                elif action == "antiguedad":
                    content = abs((datetime.datetime.today() - tuits[r].created_at).seconds // 60)
                elif action == "media":
                    content = 1 if self.has_media(tuits[r]) else 0
                else:
                    content = action.lower() in TwitterBot.getStatusText(tuits[r]).lower()
                analisis[r].append(content)
        print(len(tuits), "tuits analizados.")
        return analisis

    def like_tuits(self, max_status=10, longitud_min=1, longitud_max=9999999, lineas_min=1, lineas_max=9999999, likes_min=0, likes_max=9999999, antiguedad_min=0, antiguedad_max=9999999):
        counter = 0
        for status in self.limit_handled(tweepy.Cursor(self.api.home_timeline, tweet_mode="extended").items(limit=max_status)):
            if not (longitud_min <= len(self.getStatusText(status)) <= longitud_max):
                continue
            if not (likes_min <= status.favorite_count <= likes_max):
                continue
            if not (lineas_min <= self.getStatusText(status).count("\n") + 1 <= lineas_max):
                continue
            if not (antiguedad_min <= abs((datetime.datetime.today() - status.created_at).seconds // 60) <= antiguedad_max):
                continue
            self.api.create_favorite(status.id)
            counter += 1
        print("(TWEETBOT)", counter, "likes.")

    def analiza_timeline(self, propiedades, num=10):
        tuits = self.timeline(num)
        print("(TWITTERBOT) Analizando timeline:", end=" ")
        return self.analiza_estados(tuits, propiedades)

    def delete_unliked_status(self, min_likes=1, probability=0.5):
        if random.random() > probability:
            print("Randomly decided not to delete status because of the number of favourites.")
            return
        keeps = []
        count = 0
        for status in self.limit_handled(tweepy.Cursor(self.api.user_timeline, exclude_replies=True).items()):
            if status.id_str not in keeps:
                if random.random() < 0.5:
                    if status.favorite_count < min_likes:
                        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=70)
                        if status.created_at > cutoff_date:
                            self.api.destroy_status(status.id_str)
                            count += 1
        print("Deleted", count, "status with less than", min_likes, "like(s).")

    def follow_nonbots(self, following=700, followers=40, probability=0.5):
        if random.random() > probability:
            return
        new_follows = 0
        unfollows = 0
        for follower in self.limit_handled(tweepy.Cursor(self.api.followers).items()):
            if follower.friends_count < following and follower.followers_count > followers:
                if not follower.following:
                    if random.random() < 0.1:
                        follower.follow()
                        new_follows += 1
            if follower.friends_count > following * 2 and follower.followers_count < 5:
                if follower.following:
                    if random.random() < 0.5:
                        follower.unfollow()
                        unfollows += 1
        print("Following", new_follows, "accounts more. Unfollowed", unfollows, "accounts.")

        if random.random() < 0.5:
            print("Updating follower and followed lists.")
            self.update_lists_follows()

    @property
    def fllwr(self):
        return self._fllwr

    @fllwr.setter
    def fllwr(self, fllwr):
        self._fllwr = fllwr

    @property
    def trstd(self):
        return self._trstd

    @trstd.setter
    def trstd(self, trstd):
        self._trstd = trstd

    @property
    def fllwd(self):
        return self._fllwd

    @fllwd.setter
    def fllwd(self, fllwd):
        self._fllwd = fllwd

    def update_lists_follows(self):
        FLLWR = self.fllwr
        FLLWD = self.fllwd
        followers = []
        followeds = []
        for follower in self.limit_handled(tweepy.Cursor(self.api.followers_ids).items()):
            followers.append(follower)
        for friend in self.limit_handled(tweepy.Cursor(self.api.friends_ids).items()):
            followeds.append(friend)
        random.shuffle(followers)
        random.shuffle(followeds)
        for follower in followers[0:10]:
            try:
                self.api.add_list_member(list_id=FLLWR, user_id=follower)
            except:
                break
        for friend in followeds[0:10]:
            try:
                self.api.add_list_member(list_id=FLLWD, user_id=friend)
            except:
                break

    def get_all_lists(self):
        all_lists = []
        tries = 5
        while tries > 0:
            try:
                all_lists = self.api.lists_all()
                break
            except:
                tries -= 1
                print("Waiting for API to refresh.")
                time.sleep(60 * 15)
        return all_lists

    @staticmethod
    def count_appearances(text, lista):
        for simbolo in ["#", "!", "?", ",", ".", "  ", "¿", "¡"]:
            text = text.replace(simbolo, " ")
        count = 0
        for token in text.split(" "):
            for word in lista:
                if word.lower() == token.lower() or word.lower() + "s" == token.lower():
                    count += 1
        return count

    def acceptable_status(self, text, min_oks=0, max_und=0):
        contains_ok = TwitterBot.count_appearances(text, self.desired_words) >= min_oks
        contains_bad = TwitterBot.count_appearances(text, self.undesired_words) > max_und
        return contains_ok and not contains_bad

    def get_status_text(self, status):
        if hasattr(status, "retweeted_status"):  # Check if Retweet
            try:
                return status.retweeted_status.extended_tweet["full_text"]
            except AttributeError:
                return status.retweeted_status.full_text
        else:
            try:
                return status.extended_tweet["full_text"]
            except AttributeError:
                return status.full_text

    def like_from_lists(self, max_days=2, how_many=8):
        likes = 0
        total = 0

        for lista in self.get_all_lists():
            print("Looking at list:", lista.name, end=" ")
            # only first howMany in list
            for status in self.limit_handled(tweepy.Cursor(self.api.list_timeline, list_id=lista.id, tweet_mode="extended").items(how_many)):
                total += 1
                if "anceta" in status.author.name:
                    continue
                # if it is possibly_sensitive, pass
                if hasattr(status, 'possibly_sensitive'):
                    if status.possibly_sensitive:
                        continue
                # if its quoting an unacceptable status, pass
                if status.is_quote_status:
                    try:
                        if not self.acceptable_status(self.get_status_text(self.api.get_status(status.quoted_status_id, tweet_mode="extended")), 1):
                            continue
                    except:
                        continue
                # if it's too old or random 30%, pass
                if status.created_at < datetime.datetime.utcnow() - datetime.timedelta(days=max_days) or random.random() < 0.3:
                    continue
                # if it hasn't been liked nor re-tweeted and
                if not status.favorited and not status.in_reply_to_user_id and not status.in_reply_to_status_id:
                    if self.acceptable_status(self.get_status_text(status), 1):  # no undesired words appear in it
                        self.api.create_favorite(status.id)
                        likes += 1
            print("(" + str(likes) + " c. l.)")
        print("Of", total, "tweets from lists, only", likes, "were liked.")
        return likes, total

    def handmade_database_tweets(self, prob=0.5):
        try:
            f = open("data/database1.txt", "r", encoding="utf8")
            lines = f.read().splitlines()
            f.close()
        except:
            print("No se ha encontrado la base de datos local.")
        return True

    def handmade_drivedoc_tweets(self, prob=0.5):
        try:
            db = DriveBot()
        except:
            print("No se ha encontrado la base de datos en Drive.")
        return True

    def handmade_tweetsOld(self, prob=0.5):
        f = open("data/database.txt", "r", encoding="utf8")
        lines = f.read().splitlines()
        f.close()

        selected_tweet = []
        for tweet in lines:
            # find positions of tags
            media_start = len(tweet)
            date_start = len(tweet)
            try:
                media_start = tweet.index("{\media}")
            except:
                pass
            try:
                date_start = tweet.index("{\date}")
            except:
                pass

            # find parts of tweets
            media = ""
            days = ""
            text = tweet[0:min(media_start, date_start)]
            if media_start < date_start:
                media = tweet[media_start + 8:date_start]
                if date_start < len(tweet):
                    days = datetime.datetime.strptime(tweet[date_start + 7:], "%d-%m-%Y")
            elif media_start < len(tweet) or date_start < len(tweet):
                media = tweet[media_start + 8:]
                days = datetime.datetime.strptime(tweet[date_start + 7:media_start], "%d-%m-%Y")
            selected_tweet.append({"text": text, "media": media, "days": days})

        worked = False
        for i in range(len(selected_tweet)):
            tweet = selected_tweet[i]
            if tweet["days"] == "":
                continue
            if datetime.datetime.utcnow() - datetime.timedelta(days=1) < tweet["days"] < datetime.datetime.utcnow():
                if tweet["media"]:
                    worked = self.tweet_with_media(tweet["text"], tweet["media"])
                else:
                    worked = self.tweet_status(tweet["text"])
            if worked:
                del selected_tweet[i]
                break

        if random.random() > prob:
            print("Randomly decided that no handmade tweet will be publishing with probability:", 1 - prob)
            return

        elif not worked:
            for i in range(len(selected_tweet)):
                tweet = selected_tweet[i]
                if tweet["days"] == "":
                    hashtags = []
                    if "http" not in tweet["text"] and "#" not in tweet["text"]:
                        hashtags = self.get_important_tokens(tweet["text"])

                    text = tweet["text"]
                    for hash in hashtags:
                        text += " #" + hash
                    if tweet["media"]:
                        worked = self.tweet_with_media(text, tweet["media"])
                    else:
                        worked = self.tweet_status(text)
                if worked:
                    del selected_tweet[i]
                    break

        f = open("D:/Source/tuits/data/database.txt", "w", encoding="utf8")
        for i in range(len(selected_tweet)):
            tweet = selected_tweet[i]
            f.write(tweet["text"] + ("{\date}" + tweet["days"].strftime("%d-%m-%Y") if tweet["days"] != "" else "") + ("{\media}" + tweet["media"] if tweet["media"] else "") + ("\n" if i < len(selected_tweet) - 1 else ""))
        f.close()
        return -1

    def tweet_status(self, text):
        for status in self.limit_handled(tweepy.Cursor(self.api.user_timeline).items(10)):
            if status.text == text:
                print("You already published this, not tweeting.")
                return False
        tests = 10
        while tests > 0:
            try:
                self.api.update_status(text)
                print("Tweeted:", text)
                return True
            except:
                tests -= 1
        print("Something went wrong, not tweeting.")
        return False

    def tweet_with_media(self, text, media):
        for status in self.limit_handled(tweepy.Cursor(self.api.user_timeline).items(10)):
            if status.text == text:
                print("You already published this, not tweeting.")
                return False
        tests = 10
        while tests > 0:
            try:
                media = self.api.media_upload(media).media_id
                self.api.update_status(text, media_ids=[media])
                print("Tweeted:", text)
                return True
            except:
                tests -= 1
        print("Something went wrong, not tweeting.")
        return False

    @staticmethod
    def get_important_tokens(sentence, num=2):
        important_tokens = sentence.lower().replace("\"", " ").replace("(", " ").replace(")", " ").replace(",", " ").replace("¿", " ").replace("?", " ").replace("¡", " ").replace("!", " ").replace(".", " ").replace("!", " ").replace("  ", " ").split(" ")
        important_tokens = sorted(important_tokens, key=len)[-4:-1]
        return important_tokens[0:num]

    def music_tweet(self, client_id, client_secret, prob=0.5):
        if random.random() > prob:
            print("Randomly decided that no music tweet will be publishing with probability:", 1 - prob)
            return
        m = MusicBot(client_id, client_secret)
        text = m.get_lyrics_of_playlist_random_song(["Alan Parsons"])
        self.tweet_status(text)

    def retweet_favourite_users(self, max_days=3, how_many=10):
        # last retweet to mention
        status = self.api.user_timeline(count=1)[0]
        mention = ""
        if len(status.entities["user_mentions"]) > 0:
            mention = status.entities["user_mentions"][0]["name"]

        tuits = []
        for status in self.limit_handled(tweepy.Cursor(self.api.list_timeline, list_id=self.trstd, tweet_mode="extended").items(how_many)):
            if status.user.name != mention:
                if status.created_at > datetime.datetime.utcnow() - datetime.timedelta(days=max_days):
                    if self.acceptable_status(self.getStatusText(status)):
                        if not status.retweeted and not status.in_reply_to_status_id and not status.is_quote_status:
                            tuits += [[status.id, self.getStatusText(status)]]
        tests = 10
        while tests > 0:
            try:
                status = random.choice(tuits)
                self.api.retweet(status[0])
                print("Retweet:", status[1])
                return status[1]
            except:
                tests -= 1
        print("No se ha hecho ningún retweet.")
        return None


class DriveBot(Bot):
    def __init__(self, file=""):
        super().__init__()
        self._description = "I'm a bot that can be used to read and write Drive files!"

        auth.authenticate_user()
        gauth = GoogleAuth()
        gauth.credentials = GoogleCredentials.get_application_default()
        self.gc = gspread.authorize(gauth.credentials)
        self.drive = GoogleDrive(gauth)

        if file != "":
            self.look_for_file(file)

    def look_for_file(self, nombre_archivo):
        gfile = self.drive.ListFile({'q': "title contains '" + nombre_archivo + "'"}).GetList()[0]
        self._document = self.gc.open(gfile['title']).sheet1
        print("(DRIVEBOT) \"" + nombre_archivo + "\" abierto con éxito.")

    @property
    def document(self):
        return self._document

    def escribe(self, texto, fila, columna):
        self._document.update_cell(fila, columna, texto)

    def escribe_lista(self, lista, foc, fila, columna, titulo=""):
        if titulo != "":
            if foc == "f":
                self.escribe(titulo, fila, max(columna - 1, 1))
            else:
                self.escribe(titulo, max(fila - 1, 1), columna)
        for i in range(len(lista)):
            if foc == "f":
                self.escribe(lista[i], fila, columna + i)
            else:
                self.escribe(lista[i], i + fila, columna)

    def escribe_tabla(self, encabezados, tabla):
        self.borrar_todo()
        self.escribe_lista(["#"] + encabezados, "f", 1, 1)
        for c in range(len(tabla)):
            self.escribe(c + 1, c + 2, 1)
            self.escribe_lista(tabla[c], "f", c + 2, 2)

    def borrar_todo(self):
        self._document.clear()


class TokenEmbedding:
    def __init__(self, embedding_name):
        self.idx_to_token, self.idx_to_vec = self._load_embedding(embedding_name)
        self.unknown_idx = 0
        self.token_to_idx = {token: idx for idx, token in enumerate(self.idx_to_token)}

    def _load_embedding(self, embedding_name):
        idx_to_token, idx_to_vec = ['<unk>'], []
        data_dir = d2l.download_extract(embedding_name)
        # GloVe website: https://nlp.stanford.edu/projects/glove/
        # fastText website: https://fasttext.cc/
        with open(os.path.join(data_dir, 'vec.txt'), 'r') as f:
            for line in f:
                elems = line.rstrip().split(' ')
                token, elems = elems[0], [float(elem) for elem in elems[1:]]
                # Skip header information, such as the top row in fastText
                if len(elems) > 1:
                    idx_to_token.append(token)
                    idx_to_vec.append(elems)
        idx_to_vec = [[0] * len(idx_to_vec[0])] + idx_to_vec
        return idx_to_token, np.array(idx_to_vec)

    def __getitem__(self, tokens):
        indices = [
            self.token_to_idx.get(token, self.unknown_idx)
            for token in tokens]
        vecs = self.idx_to_vec[np.array(indices)]
        return vecs

    def __len__(self):
        return len(self.idx_to_token)


class AI():
    def __init__(self):
        self._detector = None
        self.diccionario = None

    def train(self, x, y):
        self._model = LinearRegression().fit(x, y)
        print("(IA) Modelo entrenado, listo para usar.")

    def predict(self, x):
        return self._model.predict(np.array(x).reshape(1, -1))

    def predict_likes(self, analisis):
        return [int(max(ai.predict(line), 0)) for line in analisis]

    @staticmethod
    def split(info_con_likes):
        return [data[:-1] for data in info_con_likes], [data[-1] for data in info_con_likes]

# OBJECT DETECTION PART
# ==============================================================================
# Copyright 2018 The TensorFlow Hub Authors. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

    # Pick an object detection module. FasterRCNN+InceptionResNet V2: high accuracy, ssd+mobilenet V2: small and fast.
    def init_detector(self, module="default"):
        if module == "fast":
            module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
        else:
            module_handle = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
        self._detector = hub.load(module_handle).signatures['default']

    @property
    def detector(self):
        return self._detector

    @detector.setter
    def detector(self, detector):
        self._detector = detector

    @staticmethod
    def display_image(image):
        fig = plt.figure(figsize=(7, 7))
        plt.grid(False)
        plt.imshow(image)

    def download_and_resize_image(self, url, new_width, new_height, display=False):
        _, filename = tempfile.mkstemp(suffix=".jpg")
        response = urlopen(url)
        image_data = response.read()
        image_data = BytesIO(image_data)
        pil_image = Image.open(image_data)
        pil_image = ImageOps.fit(pil_image, (new_width, new_height), Image.ANTIALIAS)
        pil_image_rgb = pil_image.convert("RGB")
        pil_image_rgb.save(filename, format="JPEG", quality=90)
        if display:
            self.display_image(pil_image)
        return filename

    def draw_bounding_box_on_image(self, image, ymin, xmin, ymax, xmax, color, font, thickness=4, display_str_list=()):
        """Adds a bounding box to an image."""
        draw = ImageDraw.Draw(image)
        im_width, im_height = image.size
        (left, right, top, bottom) = (xmin * im_width, xmax * im_width, ymin * im_height, ymax * im_height)
        draw.line([(left, top), (left, bottom), (right, bottom), (right, top), (left, top)], width=thickness, fill=color)
        display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
        total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

        if top > total_display_str_height:
            text_bottom = top
        else:
            text_bottom = top + total_display_str_height
        # Reverse list and print from bottom to top.
        for display_str in display_str_list[::-1]:
            text_width, text_height = font.getsize(display_str)
            margin = np.ceil(0.05 * text_height)
            draw.rectangle([(left, text_bottom - text_height - 2 * margin), (left + text_width, text_bottom)], fill=color)
            draw.text((left + margin, text_bottom - text_height - margin), display_str, fill="black", font=font)
            text_bottom -= text_height - 2 * margin

    def draw_boxes(self, image, boxes, class_names, scores, max_boxes=10, min_score=0.1):
        colors = list(ImageColor.colormap.values())
        font = ImageFont.load_default()
        for i in range(min(boxes.shape[0], max_boxes)):
            if scores[i] >= min_score:
                ymin, xmin, ymax, xmax = tuple(boxes[i])
                display_str = "{}: {}%".format(class_names[i].decode("ascii"), int(100 * scores[i]))
                color = colors[hash(class_names[i]) % len(colors)]
                image_pil = Image.fromarray(np.uint8(image)).convert("RGB")
                self.draw_bounding_box_on_image(image_pil, ymin, xmin, ymax, xmax, color, font, display_str_list=[display_str])
                np.copyto(image, np.array(image_pil))
        return image

    @staticmethod
    def load_img(path):
        img = tf.io.read_file(path)
        img = tf.image.decode_jpeg(img, channels=3)
        return img

    def run_detector(self, detector, path, log, display):
        img = self.load_img(path)
        converted_img = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
        result = detector(converted_img)
        result = {key: value.numpy() for key, value in result.items()}
        if display:
            image_with_boxes = self.draw_boxes(img.numpy(), result["detection_boxes"], result["detection_class_entities"], result["detection_scores"], log)
            self.display_image(image_with_boxes)
        return [r.decode('utf-8') for r in result["detection_class_entities"][0:log]]

    def detect_objects(self, image_url, new_width=500, new_height=500, objects=3, display=True):
        image_path = self.download_and_resize_image(image_url, new_width, new_height)
        return self.run_detector(self.detector, image_path, objects, display)

    def init_diccionario(self):
        npx.set_np()
        d2l.DATA_HUB['glove.6b.50d'] = (d2l.DATA_URL + 'glove.6B.50d.zip', '0b8703943ccdb6eb788e6f091b8946e82231bc4d')
        d2l.DATA_HUB['glove.6b.100d'] = (d2l.DATA_URL + 'glove.6B.100d.zip', 'cd43bfb07e44e6f27cbcc7bc9ae3d80284fdaf5a')
        d2l.DATA_HUB['glove.42b.300d'] = (d2l.DATA_URL + 'glove.42B.300d.zip', 'b5116e234e9eb9076672cfeabf5469f3eec904fa')
        d2l.DATA_HUB['wiki.en'] = (d2l.DATA_URL + 'wiki.en.zip', 'c1816da3821ae9f43899be655002f6c723e91b88')
        self.diccionario = TokenEmbedding('glove.6b.50d')

    @staticmethod
    def knn(W, x, k):
        print("x.reshape(-1,)", type(x.reshape(-1,)))
        print("np1.dot(W, x.reshape(-1,))", type(W), type(x.reshape(-1,)))
        print("np1.sum(W * W, axis=1)", np1.sum(W * W, axis=1))
        print("np1.sqrt(np1.sum(W * W, axis=1) + 1e-9)", np1.sqrt(np1.sum(W * W, axis=1) + 1e-9))
        print("np1.sqrt((x * x).sum())", np1.sqrt((x * x).sum()))

        cos = np1.dot(W, x.reshape(-1,)) / (np1.sqrt(np1.sum(W * W, axis=1) + 1e-9) * np1.sqrt((x * x).sum()))
        topk = npx.topk(cos, k=k, ret_typ='indices')
        return topk, [cos[int(i)] for i in topk]

    def palabras_similares(self, query_token, k=3):
        print("HERE")
        topk, cos = self.knn(self.diccionario.idx_to_vec, self.diccionario[[query_token]], k + 1)
        palabras = []
        for i, c in zip(topk[1:], cos[1:]):
            print(self.diccionario.idx_to_token[int(i)])
            palabras.append(self.diccionario.idx_to_token[int(i)])
        return palabras
