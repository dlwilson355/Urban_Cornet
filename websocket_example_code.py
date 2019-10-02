
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  1 08:32:06 2019
@author: sarafergus
"""
  
# https://github.com/websocket-client/websocket-client

import websocket
import sqlite3
import json
import requests
try:
    import thread
except ImportError:
    import _thread as thread
from botsettings import API_TOKEN

action = ""

#def create_connection(db_file):
#    """ create a database connection to a SQLite database """
#    conn = None
#    try:
#        conn = sqlite3.connect(db_file)
#        print(sqlite3.version)
#    except Error as e:
#        print(e)
#    finally:
#        if conn:
#            conn.close()
#def create_connection():
#    """ create a database connection to a database that resides
#        in the memory
#    """
#    conn = None;
#    try:
#        conn = sqlite3.connect(':memory:')
#        print(sqlite3.version)
#    except Error as e:
#        print(e)
#    finally:
#        if conn:
#            conn.close()


def on_message(ws, message):
    category_actions = ['time', 'pizza', 'greet', 'weather', 'joke']
    global action

    # these print statements are only temporary for debugging
    print("Message Payload...")
    print(message)
    print("Relevant Message Content...")
    print(get_message_content(message))

    message_content = get_message_content(message)

    if "acknowledge" in message_content:
        send_message(ws, "Acknowledged")

    if "training" in message_content:
        action = 'training'
        send_message(ws, "OK, I'm ready for training. What NAME should this ACTION be?")

    if 'done' in message_content:
        action = 'done'
        send_message(ws, "OK, I'm finished training")

    if len(message_content) > 0 and action in category_actions:
        put_in_db(message)
        send_message(ws, "OK, I've got it! What else?")

    if "time" in message_content and action == 'training':
        action = 'time'

    if "pizza" in message_content and action == 'training':
        action = 'pizza'

    if "greet" in message_content and action == 'training':
        action = 'greet'

    if "weather" in message_content and action == 'training':
        action = 'weather'

    if "joke" in message_content and action == 'training':
        action = 'joke'


def put_in_db(message):
    global action
    conn = sqlite3.connect("name.db")
    c = conn.cursor()
    c.execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (message, action,))
    conn.commit()  # save (commit) the changes\


def make_table(database):
    conn = sqlite3.connect("name.db")
    c = conn.cursor() 
    c.execute(database)
    conn.commit()


def send_message(ws, text):
    """Sends a message over the project01 channel with the specified text."""

    dict_payload = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": text}
    json_payload = json.dumps(dict_payload)
    ws.send(json_payload)


def get_message_content(message):
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


def on_error(ws, error):
    print("in on error")

    print('The error is:', error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    send_message(ws, "Jarvis is online. ;)")


if __name__ == "__main__":
    # create an empty database
    sql_create_training_data_table = """ CREATE TABLE IF NOT EXISTS training_data (
                                             txt text,
                                             action text
                                        ); """
    make_table(sql_create_training_data_table)

    # create the connection string
    connect_string = f"http://slack.com/api/rtm.connect"
    url_string = requests.get(connect_string, params={'token': API_TOKEN}).json()['url']

    # create the connection
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(url_string,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
