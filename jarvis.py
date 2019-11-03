"""
Authors: Daniel Wilson, Sarah Fergus, Noah Stracqualursi
This file contains the code for running a slack bot (Jarvis).
It uses the python website client to connect to Slack's RTM API.
"""


import websocket
import sqlite3
import json
import requests
import sklearn
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from botsettings import API_TOKEN


class Jarvis:
    def __init__(self):
        self.action = ""
        self.db_connection, self.db_cursor = self.initialize_database()
        self.ws_connection = self.initialize_slack_connection()
        self.ws_connection.run_forever()

    def initialize_database(self):
        """This function connects Jarvis to the database."""

        connection = sqlite3.connect("jarvis.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS training_data "
                       "(txt text, action text)")

        return connection, cursor

    def initialize_slack_connection(self):
        """This function connects Jarvis to Slack over the RTM API."""

        # get the url string
        connect_string = f"http://slack.com/api/rtm.connect"
        url_string = requests.get(connect_string,
                                  params={'token': API_TOKEN}).json()['url']

        # create the connection and set up the websocket
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            url_string,
            on_message=lambda ws, mes: self.on_message(mes),
            on_error=lambda ws, err: self.on_error(err),
            on_close=lambda ws: self.on_close())
        ws.on_open = lambda ws: self.on_open()

        return ws

    def on_message(self, message):
        """Controls a bot's response to receiving a message."""

        category_actions = ['time', 'pizza', 'greet', 'weather', 'joke']
        message_content = self.get_message_content(message)

        # check if training should start
        if "training" in message_content:
            self.action = 'training'
            self.send_message("OK, I'm ready for training. "
                              "What NAME should this ACTION be?")

        # check if training should stop
        elif 'done' in message_content:
            self.action = 'done'
            self.send_message("OK, I'm finished training")

        # check if new message should be learned
        elif self.action in category_actions and message_content:
            self.add_to_database((message_content, self.action))
            self.send_message("OK, I've got it! What else?")

        # check if new action should be learned
        elif self.action == 'training' and message_content:
            self.action = message_content
            self.send_message(f"OK, Let's call this action `{self.action.upper()}`. "
                              "Now give me some training text!")

    def add_to_database(self, entities):
        """This function adds the passed entities to Jarvis' database."""

        # execute the sql command to modify the table
        self.db_cursor.execute("INSERT INTO training_data(txt, action) "
                               "VALUES(?, ?)", entities)

        # commit the changes
        self.db_connection.commit()

    def send_message(self, text):
        """Sends a message with the specified text."""

        dict_payload = {"id": 1,
                        "type": "message",
                        "channel": "CNPJBJZ29",
                        "text": text}
        json_payload = json.dumps(dict_payload)
        self.ws_connection.send(json_payload)

    def get_message_content(self, message):
        """
        Returns a string containing the text of a message typed by the user.

        The returned message will be converted to lowercase.
        Any unneeded punctuation will be removed.
        Returns an empty string if the message was sent by Jarvis.
        This prevents Jarvis from responding to his own messages.
        """

        punctuation_to_remove = "~!@#$%^&*()-+=,./<>"
        json_payload = json.loads(message)
        if "client_msg_id" in json_payload.keys():
            text = json_payload["text"].lower()
            for character in punctuation_to_remove:
                text = text.replace(character, "")
            return text
        return ""

    def on_open(self):
        """Sends a message when opening a connection."""

        self.send_message("Jarvis is online. ;)")

    def on_close(self):
        """Called when the web socket is closed."""

        print("### closed ###")

    def on_error(self, error):
        """Prints an error encountered by the bot."""

        print("in on error")
        print('The error is:', error)

    def get_pipeline(self):
        """Returns the pipeline used in Jarvis' brain."""

        raise NotImplementedError

    def train(self, X, Y):
        """Calling this function makes Jarvis train his brain."""

        raise NotImplementedError

    def evaluate(self, X):
        """Jarvis will evaluate the data and return the corresponding predictions."""

        raise NotImplementedError

    def get_database_data(self):
        """Returns the data stored in Jarvis' database."""

        raise NotImplementedError

    def get_data_from_files(self, dir_path):
        """Returns the data from the files in the directory."""

        raise NotImplementedError


if __name__ == "__main__":
    jarvis = Jarvis()
