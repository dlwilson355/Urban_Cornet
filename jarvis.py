"""
Authors: Daniel Wilson, Sarah Fergus, Noah Stracqualursi
This file contains the code for running a slack bot (Jarvis).
It uses the python website client to connect to Slack's RTM API.
"""


import websocket
import sqlite3
import json
import requests
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

        if "training" in message_content:
            self.action = 'training'
            self.send_message("OK, I'm ready for training. "
                              "What NAME should this ACTION be?")

        elif 'done' in message_content:
            self.action = 'done'
            self.send_message("OK, I'm finished training")

        elif len(message_content) > 0 and self.action in category_actions:
            self.add_to_database((message_content, self.action))
            self.send_message("OK, I've got it! What else?")

        elif "time" == message_content and self.action == 'training':
            self.action = 'time'
            self.send_message("OK, Let's call this action `TIME`. "
                              "Now give me some training text!")

        elif "pizza" == message_content and self.action == 'training':
            self.action = 'pizza'
            self.send_message("OK, Let's call this action `PIZZA`. "
                              "Now give me some training text!")

        elif "greet" == message_content and self.action == 'training':
            self.action = 'greet'
            self.send_message("OK, Let's call this action `GREET`. "
                              "Now give me some training text!")

        elif "weather" == message_content and self.action == 'training':
            self.action = 'weather'
            self.send_message("OK, Let's call this action `WEATHER`. "
                              "Now give me some training text!")

        elif "joke" == message_content and self.action == 'training':
            self.action = 'joke'
            self.send_message("OK, Let's call this action `JOKE`. "
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


if __name__ == "__main__":
    jarvis = Jarvis()
