#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 19:05:46 2019

@author: sarafergus
"""

"""
Authors: Daniel Wilson, Sara Fergus, Noah Stracqualursi
This file contains the code for running a slack bot (Jarvis).
It uses the python website client to connect to Slack's RTM API.
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

'''
TODO: commenting
TODO: directions are not always working
TODO: go is not returning False when it should
TODO: Fix indexing issues
TODO: write out 'help' response
TODO: create 'done' response in game
TODO: learning?
TODO: input validation
'''

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
        self.play_game = False
        self.boats = {'battleship' : 0, 'submarine': 0}
        self.bow = ''
        self.current_boat = ''
        self.direction = ''
        self.confirm = False
        self.guess_board = battleship.load_gameboard()
        self.jarvis_board = battleship.load_gameboard()
        self.create_jarvis_board()
        self.player_board = battleship.load_gameboard()
        
        # Don't initialize attributes after this point
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

        message_content = self.get_message_content(message)

        # check if training should start
        if 'training time' in message_content:
            self.action = 'training'
            self.send_message("OK, I'm ready for training. "
                              "What NAME should this ACTION be?")
        # check if testing should start
        elif 'testing time' in message_content:
            self.train()
            self.action = 'testing'
            self.send_message("OK, I'm ready for testing. Write me something and I'll try to figure it out.")
        
        elif 'battleship time' in message_content:
            self.play_game = True
            self.action = 'place_boat'
            self.send_message("Let's play!")
            for item in self.boats.keys():
                if self.boats[item] == 0:
                   self.boats[item] = 1
                   self.current_boat = item
                   self.show_board(self.player_board)
                   self.send_message("Place your " +item + ". Type in your bow coordinate (ex. A3). I promise I won't cheat ;)")
                   self.action = 'place_boat'
                   break
                if 0 not in self.boats.values():
                   self.action = 'play'
                   self.send_message('Time to play. I hope you are ready to lose.')
                   self.send_message('You go first. Here is your guess board. Where would you like to shoot?')
                   self.show_board(guess_board)
                   
        elif self.play_game == True and self.action == 'start_over':
             for item in self.boats.keys():
                if self.boats[item] == 0:
                   self.boats[item] = 1
                   self.action = 'place_boat'
                   break
                if 0 not in self.boats.values():
                   self.action = 'play'
                   self.send_message('Time to play. I hope you are ready to lose.')
                   self.send_message('You go first. Here is your guess board. Where would you like to shoot?')
                   self.show_board(guess_board) 
                   
        elif self.play_game== True and self.action == 'place_boat' and 'message' in message:
            self.bow = message_content
            self.send_message("Sweet. In what cardinal direction (N, S, W, E) is your boat traveling?")
            self.action = 'direction'

        elif self.play_game == True and self.action == 'direction' and 'message' in message:
            letter2dir = {'N': 'north','n': 'north', 'S': 'south', 'E': 'east', 'W':'west', 's': 'south', 'e': 'east', 'w':'west'}
            self.direction = message_content
            self.send_message("You would like your "+ self.current_boat+ " at "+ self.bow +  ' facing '+ letter2dir[self.direction] + ". Confirm? (Y/N)")
            self.action = 'confirm'
            
        elif self.play_game == True and self.action == 'confirm' and 'message' in message:
            if message_content == 'y':
                self.send_message("Great! Here is your current board:")
                self.create_board()
                if 0 in self.boats.values():
                    for boat in self.boats.keys():
                        if self.boats[boat] == 0:
                            self.current_boat = boat
                            self.send_message("Alright. Place your " +self.current_boat + ". Type in your bow coordinate (ex. A3).")
            else:
                self.boats[self.current_boat] = 0
                self.send_message("Alright. Place your " +self.current_boat + ". Type in your bow coordinate (ex. A3).")
            self.action = 'start_over'
                
        # check if Jarvis' brain should be loaded
        elif 'load brain' in message_content:
            self.load_brain()
            self.action = 'testing'
            self.send_message("I've loaded my brain and am ready for testing. "
                              "Write me something and I'll try to figure it out.")
            
        # check if training or testing should stop
        elif 'done' in message_content:
            #if jarvis is playing battleship, stop playing
            if self.play_game == True:
                self.send_message("Okay, let's play again soon!")
                self.play_game = False
            else:
                # if action is one of the labels, it means Jarvis is training
                if self.action in LEARNABLE_ACTIONS:
                    self.action = 'training'
                self.send_message(f"OK, I'm finished {self.action}.")
                self.action = 'done'

        # check if new message should be learned
        elif self.action in LEARNABLE_ACTIONS and message_content:
            self.add_to_database((message_content, self.action))
            self.send_message("OK, I've got it! What else?")

        # check if new action should be learned
        elif self.action == 'training' and message_content:
            self.action = message_content.upper()
            self.send_message(f"OK, Let's call this action `{self.action}`. "
                              "Now give me some training text!")
            
        # check if a prediction should be made
        elif self.action == 'testing' and message_content:
            self.send_message(f"OK, I think the action you mean is `{self.predict(message_content)}`...\n"
                              "Write me something else and I'll try to figure it out.")

        elif self.play_game == True and 'help' in message_content:
            self.send_message('TODO: put in steps on how to play')
        
        elif self.play_game == True and self.action == 'play':
            cont = "Already fired there, please choose new coordinates."
            while cont == "Already fired there, please choose new coordinates.":
                result = battleship.fire(message_content,self.guess_board , self.jarvis_board)
                self.guess_board = result[1]
                self.send_message(result[0])
                #determine whether someone has won
                self.show_board(result[1])
                self.jarvis_board = result[2]
                cont = result[0]
            cont = "Already fired there, please choose new coordinates."
            self.send_message('My turn')
            #make it so that these results change point of view
            while cont ==  "Already fired there, please choose new coordinates.":  
                #change so that they cannot guess less than 1
                guess= random.choice(['a','b','c','d'])+ str(random.randint(0,3))
                result = battleship.fire(guess, None , self.player_board)
                cont = result[0]
            self.send_message('My guess is ' + guess)
            self.send_message(result[0])
            #determine whether someone has won
            self.player_board = result[3]
            self.send_message('Here your board with my guess')
            self.show_board(self.player_board)
            #if no one has won
            self.send_message('Your turn again. Where would you like to fire?')
            
            
            
            
            
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
    
    def create_board(self):            
        boat2length = {'battleship': 2, 'submarine' :3}
        boat2num = {'battleship': 'b', 'submarine':'s'}
        self.player_board, go = battleship.place_boat(self.current_boat, self.bow, self.direction, self.player_board, boat2length, boat2num)
        if go == False:
            self.send_message('You cannot place your boat there. Try again')
            self.boats[self.current_boat] = 0                
        else:
            self.show_board(self.player_board)
        self.action = 'start_over'

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

        print("Experienced an error.\n"
              f"The error is: {error}.")      
        
    def create_jarvis_board(self):
        boat2length = {'battleship': 2, 'submarine' :3}
        boat2num = {'battleship': 'b', 'submarine':'s'}
        for item in self.boats.keys():
            go = False
            while go == False:
                #this could be changed so that Jarvis can learn and get better. For now, it is entirely random.
                self.jarvis_board, go = battleship.place_boat(item, random.choice(['a','b','c','d'])+ str(random.randint(0,3)), random.choice(['n','s','e','w']), self.jarvis_board, boat2length, boat2num)
        
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

        # get the data
        x_train, x_test, y_train, y_test = self.get_training_and_testing_data(test_proportion)

        # fit the classifier
        self.classifier.fit(x_train, y_train)
        print(f"Got a mean cross validation accuracy of {self.classifier.best_score_:.4f}.")
        print(f"The parameters that worked best were {self.classifier.best_params_}.")

        # test the brain
        FIG_SAVE_PATH = "confusion_matrix.png"
        y_pred = self.classifier.predict(x_test)
        print("Here is a classification report on the testing data...")
        print(classification_report(y_test, y_pred))
        cm = confusion_matrix(y_test, y_pred)
        print("Here is the confusion matrix of the testing data.")
        print(cm)

        # save a confusion matrix
        fig = plt.figure()
        ax = fig.add_subplot(111)
        cm_ax = ax.matshow(cm)
        ax.set_xticklabels([""] + list(self.classifier.classes_))
        ax.set_yticklabels([""] + list(self.classifier.classes_))
        fig.colorbar(cm_ax)
        plt.title("Confusion Matrix")
        plt.xlabel("Predicted Label")
        plt.ylabel("True Label")
        fig.savefig(FIG_SAVE_PATH)
        print(f"Saved confusion matrix to '{FIG_SAVE_PATH}'.")

        # save the brain
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
    
    def show_board(self, board):
        b = '*    1     2    3    4\n'
        letters = ['A    ', 'B    ', 'C    ', 'D    ']
        for line in board:
            b = b + letters[0]
            letters.remove(letters[0])
            for item in line:
                b = b + str(item) + '    '
            b = b + '\n'
        self.send_message(b)
    
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
