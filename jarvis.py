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
import matplotlib.pyplot as plt
import numpy as np
import requests
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import confusion_matrix, classification_report
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
        self.channel = ""
        self.classifier = self.get_model()
        self.db_connection, self.db_cursor = self.initialize_database()
        self.ws_connection = self.initialize_slack_connection()
        self.play_game = False
        self.boats = {'battleship': 0, 'carrier': 0, 'cruiser': 0, 'submarine': 0, 'destroyer':0}
        self.bow = 'a3'
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
        # check if testing should startf
        elif 'testing time' in message_content:
            self.train_and_test()
            self.action = 'testing'
            self.send_message("OK, I'm ready for testing. Write me something and I'll try to figure it out.")
                
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
                
        elif 'battleship time' in message_content and 'help' not in message_content and 'reference' not in message_content:
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
               self.show_board(self.guess_board)
                   
        elif self.play_game == True and self.action == 'start_over'  and 'help' not in message_content and 'reference' not in message_content:
            #check on this
            dont_stop = False
            for item in self.boats.keys():
                if self.boats[item] == 0:
                   self.boats[item] = 1
                   self.action = 'place_boat'
                   dont_stop = True
                   break
            if 0 not in self.boats.values() and dont_stop == False:
               self.action = 'play'
               self.send_message('Time to play. I hope you are ready to lose.')
               self.send_message('You go first. Here is your guess board. Where would you like to shoot?')
               self.show_board(self.guess_board) 
                   
        elif self.play_game== True and self.action == 'place_boat' and 'message' in message  and 'help' not in message_content and 'reference' not in message_content:
            self.bow = message_content
            self.send_message("Sweet. In what cardinal direction (N, S, W, E) is your boat traveling?")
            self.action = 'direction'

        elif self.play_game == True and self.action == 'direction' and 'message' in message  and 'help' not in message_content and 'reference' not in message_content:
            letter2dir = {'N': 'north','n': 'north', 'S': 'south', 'E': 'east', 'W':'west', 's': 'south', 'e': 'east', 'w':'west'}
            self.direction = message_content
            self.send_message("You would like your "+ self.current_boat+ " at "+ self.bow +  ' facing '+ letter2dir[self.direction] + ". Confirm? (Y/N)")
            self.action = 'confirm'
            
        elif self.play_game == True and self.action == 'confirm' and 'message' in message  and 'help' not in message_content and 'reference' not in message_content:
            if message_content == 'y':
                self.send_message("Great! Here is your current board:")
                self.create_board()
                if 0 in self.boats.values():
                    for boat in self.boats.keys():
                        if self.boats[boat] == 0:
                            self.current_boat = boat
                            self.send_message("Alright. Place your " +self.current_boat + ". Type in your bow coordinate (ex. A3).")
                            break
            else:
                self.boats[self.current_boat] = 0
                self.send_message("Alright. Place your " +self.current_boat + ". Type in your bow coordinate (ex. A3).")
            self.action = 'start_over'
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

        elif self.play_game == True and 'help' in message_content and 'reference' not in message_content:
            self.send_message('Welcome to Battleship! How to Play:\n\n (1) Place your ships. You have 5 ships of different sizes, and you will place the bow (front), and the specify the cardinal direction in which the boat is traveling\n (2) Play the game! You and Jarvis will each take turns "firing" in an attempt to sink all of the other player\'s ships. Whoever sinks all ships first wins!\n\nTo exit the game, you can type \'done\' at any time. For a reference sheet of boats and sizes, type \'reference\' ')
        
        elif self.play_game == True and 'reference' in message_content and 'help' not in message_content:
            self.send_message('BATTLESHIP, length: 4, identifier: b\n CARRIER, length: 5, identifier:c\n CRUISER, length: 3, identifier: u\n SUBMARINE, length: 3, identifier: s\n DESTORYER,  length: 2, identifier: d')
         
        elif self.play_game == True and self.action == 'play'  and 'help' not in message_content and 'reference' not in message_content:
            result = battleship.fire(message_content,self.guess_board , self.jarvis_board)
            if result[0] == 'Winner!':
                self.send_message("You win! Congratulations! Type 'battleship time' to play again.")
                self.play_game = False
            if self.play_game == True and result[0]!= "Already fired there, please choose new coordinates.":
                self.guess_board = result[1]
                self.send_message(result[0])
                self.send_message('Guess Board:')
                self.show_board(result[1])
                self.jarvis_board = result[2]
                guess= random.choice(['a','b','c','d', 'e','f','g','h','i','j'])+ str(random.randint(0,9))
                cont = "Already fired there, please choose new coordinates."
                while cont == "Already fired there, please choose new coordinates.":
                    result = battleship.fire(guess, None , self.player_board)
                    cont = result[0]
                self.send_message('My turn. My guess is ' + guess)
                if result[0] == 'Winner!':
                        self.send_message("I win! Type 'battleship time' to play again.")
                        self.play_game = False
                if self.play_game == True:
                    self.send_message(result[0])
                    self.player_board = result[2]
                    self.send_message('Here your board with my guess')
                    self.show_board(self.player_board)
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
                        "channel": self.channel,
                        "text": text}
        json_payload = json.dumps(dict_payload)
        self.ws_connection.send(json_payload)
    
    def create_board(self):            
        boat2length= {'battleship': 4, 'carrier': 5, 'cruiser': 3, 'submarine': 3, 'destroyer':2}
        boat2num = {'battleship': 'b', 'carrier': 'c', 'cruiser': 'u', 'submarine': 's', 'destroyer':'d'}
        self.player_board, go = battleship.place_boat(self.current_boat, self.bow, self.direction, self.player_board, boat2length, boat2num)
        if go == False:
            self.send_message('You cannot place your boat there. Try again')
            self.boats[self.current_boat] = 0    
            self.show_board(self.player_board)            
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
        This function also updates self.channel to indicate the most recent
        channel a message was sent over.
        """

        punctuation_to_remove = "~!@#$%^&*()-+=,./<>"
        json_payload = json.loads(message)
        if "client_msg_id" in json_payload.keys():
            text = json_payload["text"].lower()
            for character in punctuation_to_remove:
                text = text.replace(character, "")
            self.channel = json_payload["channel"]
            return text
        return ""

    def on_open(self):
        """Prints an acknowledgement when opening a connection."""

        print("Jarvis is online. ;)")

    def on_close(self):
        """Called when the web socket is closed."""

        print("### closed ###")

    def on_error(self, error):
        """Prints an error encountered by the bot."""

        print("Experienced an error.\n"
              f"The error is: {error}.")      
        
    def create_jarvis_board(self):
        boat2length= {'battleship': 4, 'carrier': 5, 'cruiser': 3, 'submarine': 3, 'destroyer':2}
        boat2num = {'battleship': 'b', 'carrier': 'c', 'cruiser': 'u', 'submarine': 's', 'destroyer':'d'}
        for item in self.boats.keys():
            go = False
            while go == False:
                #this could be changed so that Jarvis can learn and get better. For now, it is entirely random.
                self.jarvis_board, go = battleship.place_boat(item, random.choice(['a','b','c','d', 'e','f','g','h','i','j'])+ str(random.randint(1,10)), random.choice(['n','s','e','w']), self.jarvis_board, boat2length, boat2num)
        
#    def play(self, b1, b2):
#        won = False
#        winner = 'jarvis'
#        while won == False:
#            #location = do the thing where you ask the player
#            b2, won = battleship.fire(location, b2)
#            if won == True:
#                winner = 'player'
#                break
#            b1, won = battleship.fire([random.choice['a','b','c','d', 'e','f','g','h','i','j'], random.randint(0,9)],b1)
#        self.send_message(winner + 'wins! Would you like to play again?')
        
        
        
    def train_and_test(self, test_proportion=0.2):
        """Calling this function makes Jarvis train his brain."""

        self.send_message("I'm training my brain with the data you've already given me...")

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
        cm_ax = ax.matshow(np.log(cm + .01))  # we add .01 to avoid dividing by 0 error
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

    def get_training_and_testing_data(self, testing_proportion=0.2):
        """
        Returns a tuple contains lists of data.
        The ordering is x_train, x_test, y_train, y_test.
        """

        # load and merge the data sources
        x_db, y_db = self.get_database_data()
        x_files, y_files = self.get_data_from_files()
        all_x, all_y = x_db + x_files, y_db + y_files

        return train_test_split(all_x, all_y, test_size=testing_proportion)

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
        b = '*    1     2    3    4    5    6    7    8   9    10\n'
        letters = ['A    ', 'B    ', 'C    ', 'D    ', 'E    ','F    ','G    ','H    ','I     ','J     ']
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
