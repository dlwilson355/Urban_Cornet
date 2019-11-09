#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 19:05:46 2019

@author: sarafergus
"""

"""
Authors: Daniel Wilson, Sarah Fergus, Noah Stracqualursi
This file contains the code for running a slack bot (Jarvis).
It uses the python website client to connect to Slack's RTM API.
TODO: Finish implementing "brain."
TODO: Add enumerated variable for states.
TODO: Make it so bot channel is no longer hard wired.
TODO: Experiment with different models and hyperparameters.
"""


import websocket
import random
import sqlite3
import json
import battleship 
import requests
import sklearn
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, train_test_split, cross_validate
import pickle
import os
from botsettings import API_TOKEN


# some global settings controlling Jarvis' behavior
BRAIN_SAVE_FILE_PATH = "jarvis_URBANCORNET.pkl"
DATA_DIRECTORY = "data"
DATABASE_FILE_PATH = "jarvis.db"
LEARNABLE_ACTIONS = ['TIME', 'PIZZA', 'GREET', 'WEATHER', 'JOKE']


class Jarvis:
    def __init__(self):
        self.action = ""
        self.classifier = self.get_model()
        self.db_connection, self.db_cursor = self.initialize_database()
        self.ws_connection = self.initialize_slack_connection()
        self.ws_connection.run_forever()

    def initialize_database(self):
        """This function connects Jarvis to the database."""

        connection = sqlite3.connect(DATABASE_FILE_PATH)
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

        message_content, message_channel = self.get_message_info(message)

        # check if training should start
        if 'training time' in message_content:
            self.action = 'training'
            self.send_message("OK, I'm ready for training. "
                              "What NAME should this ACTION be?",
                              message_channel)

        # check if testing should start
        elif 'testing time' in message_content:
            self.train()
            self.action = 'testing'
            self.send_message("OK, I'm ready for testing. "
                              "Write me something and I'll try to figure it out.",
                              message_channel)
        
        elif 'battleship time' in message_content:
            self.play_battleship()
            self.action = 'battleship'
            self.send_message("Let's play! Set up your board",
                              message_channel)

        elif 'test buttons' in message_content:
            self.send_message("Sending buttons test...", message_channel)
            self.send_buttons()
            self.send_message("Sent!", message_channel)

        # check if Jarvis' brain should be loaded
        elif 'load brain' in message_content:
            self.load_brain()
            self.action = 'testing'
            self.send_message("I've loaded my brain and am ready for testing. "
                              "Write me something and I'll try to figure it out.",
                              message_channel)

        # check if training or testing should stop
        elif 'done' in message_content:
            # if action is one of the labels, it means Jarvis is training
            if self.action in LEARNABLE_ACTIONS:
                self.action = 'training'
            self.send_message(f"OK, I'm finished {self.action}.", message_channel)
            self.action = 'done'

        # check if new message should be learned
        elif self.action in LEARNABLE_ACTIONS and message_content:
            self.add_to_database((message_content, self.action))
            self.send_message("OK, I've got it! What else?", message_channel)

        # check if new action should be learned
        elif self.action == 'training' and message_content:
            self.action = message_content.upper()
            self.send_message(f"OK, Let's call this action `{self.action}`. "
                              "Now give me some training text!",
                              message_channel)

        # check if a prediction should be made
        elif self.action == 'testing' and message_content:
            self.send_message(f"OK, I think the action you mean is `{self.predict(message_content)}`...\n"
                              "Write me something else and I'll try to figure it out.",
                              message_channel)

        elif self.action == 'battleship' and 'help' in message_content:
            self.send_message('TODO: put in steps on how to play',
                              message_channel)
            
    def add_to_database(self, entities):
        """This function adds the passed entities to Jarvis' database."""

        # execute the sql command to modify the table
        self.db_cursor.execute("INSERT INTO training_data(txt, action) "
                               "VALUES(?, ?)", entities)

        # commit the changes
        self.db_connection.commit()

    def send_message(self, text, channel='CNPJBJZ29'):
        """Sends a message with the specified text."""

        dict_payload = {"id": 1,
                        "type": "message",
                        "channel": channel,
                        "text": text}
        json_payload = json.dumps(dict_payload)
        self.ws_connection.send(json_payload)

    def send_buttons(self):
        """Creates a button in the chat."""

        dict_payload = {
                        "channel": "CNPJBJZ29",
                        "text": "Sent",
                        "blocks": [{
                        "type": "actions",
                        "elements": [
                            {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reply to review",
                                "emoji": "false"
                                }
                            }
                          ]
                        }]
                        }

        json_payload = json.dumps(dict_payload)
        self.ws_connection.send(json_payload)

    def get_message_info(self, message):
        """
        Returns a tuple.
        The first index contains a string representing the message typed by the user.
        The second index contains the ID of the channel over which it was sent.
        The returned message will be converted to lowercase.
        Any unneeded punctuation will be removed.
        Returns an empty string if the message was sent by Jarvis.
        This prevents Jarvis from responding to his own messages.
        """

        punctuation_to_remove = "~!@#$%^&*()-+=,./<>"
        json_payload = json.loads(message)
        print(json_payload)
        if 'client_msg_id' in json_payload.keys():
            text = json_payload['text'].lower()
            for character in punctuation_to_remove:
                text = text.replace(character, "")
            return text, json_payload['channel']
        return "", ""

    def on_open(self):
        """Sends a message when opening a connection."""

        self.send_message("Jarvis is online. ;)")

    def on_close(self):
        """Called when the web socket is closed."""

        print("### closed ###")

    def on_error(self, error):
        """Prints an error encountered by the bot."""

        print("Experienced an error.\n"
              f"The error is: {error}.")

    def play_battleship(self):
        #TODO: make direction dictionary
        b1, b2 = battleship.start_game()
        #b1 = call function that tells the user to put their boats down
        for item in boats:
            go = False
            while go == False:
                b2, go = battleship.place_boat(item, [random.randint(0,3), random.randint(0,3)], b2, num2dir[random.randint(0,3)], boat2length, boat2num)
        self.send_message("I am ready to win. Let's go. You go first.")
        #call function play(self, b1, b2)
    
    def play(self, b1, b2):
        won = False
        winner = 'jarvis'
        while won == False:
            #location = do the thing where you ask the player
            b2, won = battleship.fire(location, b2)
            if won == True:
                winner = 'player'
                break
            b1, won = battleship.fire([random.choice['a','b','c','d'], random.randint(0,3)],b1)
        self.send_message(winner + 'wins! Would you like to play again?')
        
        
        
    def train(self):
        """Calling this function makes Jarvis train his brain."""

        self.send_message("I'm training my brain with the data you've already given me...")

        # load and merge the data sources
        x_db, y_db = self.get_database_data()
        x_files, y_files = self.get_data_from_files()
        all_x, all_y = x_db + x_files, y_db + y_files
        #x_train, x_test, y_train, y_test = train_test_split(all_x, all_y, test_size=0.25)

        # fit the classifier
        #scores = cross_validate(self.classifier, all_x, all_y, cv=10)
        #self.send_message(f"I got a mean cross validation accuracy of {scores['test_score'].mean():.2f}.")
        self.classifier.fit(all_x, all_y)
        self.send_message(f"I got a mean cross validation accuracy of {self.classifier.best_score_:.4f}.")
        self.send_message(f"These were the parameters that worked best were {self.classifier.best_params_}.")

        # save the resulting brain
        self.save_brain()

    def predict(self, text):
        """Jarvis will evaluate the text and return the corresponding prediction."""

        return self.classifier.predict([text])[0]

    def get_model(self):
        """Returns the model used in Jarvis' brain."""

        pipeline = Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', SGDClassifier()),
        ])

        params = {
            'vect__ngram_range': [(1, 1), (1, 2)],
            'tfidf__use_idf': (True, False),
            'clf__loss': ('hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron'),
            'clf__alpha': (1e-2, 1e-3),
            'clf__penalty': ('none', 'l1', 'l2', 'elasticnet'),
            'clf__early_stopping': (True, False),
        }

        model = GridSearchCV(pipeline, params, iid=False, cv=10, n_jobs=-1)

        return model

    def get_database_data(self):
        """Returns the data stored in Jarvis' database."""

        # load the data from the database
        self.db_cursor.execute("SELECT * from training_data")
        data = self.db_cursor.fetchall()

        # sort the messages and labels
        x, y = [], []
        for row in data:
            x.append(row[0])
            y.append(row[1])

        return x, y

    def get_data_from_files(self):
        """Returns the data from the files in the directory."""

        x, y = [], []

        # iterate through the data files, open the file, and read and strip the lines
        for file_path in os.listdir(DATA_DIRECTORY):
            with open(os.path.join(DATA_DIRECTORY, file_path), 'r', encoding="utf8") as f:
                for line in f.readlines():
                    line = line.strip()

                    # check if it is formatted as json and load it accordingly
                    if line[0] == "{" and line[-1] == "}":
                        data_dict = json.loads(line)
                        text = data_dict["TXT"]
                        label = data_dict["ACTION"]

                    # otherwise parse the string
                    else:
                        splits = line.split(",")
                        text = ",".join(splits[:-1])
                        label = splits[-1]

                    # append the text and label
                    x.append(text)
                    y.append(label)

        return x, y

    def convert_labels(self):
        """Converts labels between ints and their corresponding strings."""

        raise NotImplementedError

    def save_brain(self):
        """Saves Jarvis' brain to a file."""

        pickle.dump(self.classifier, open(BRAIN_SAVE_FILE_PATH, 'wb'))

    def load_brain(self):
        """Loads Jarvis' brain from a file."""

        self.classifier = pickle.load(open(BRAIN_SAVE_FILE_PATH, 'rb'))


if __name__ == "__main__":
    jarvis = Jarvis()
