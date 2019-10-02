
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
print(websocket.__file__)
import requests
from botsettings import API_TOKEN
try:
    import thread
except ImportError:
    import _thread as thread
import time
sqlite3 
action = ""
from sqlite3 import Error
 
 
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
    global action
    print(message)
    if "awknowledge" in message:
        to_send = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": "Awknowledged!"}
        to_send = json.dumps(to_send)
        ws.send(to_send)
    if "training" in message and 'reply_to' not in message:
        action = 'training'
        to_send = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": "OK, I'm ready for training. What NAME should this ACTION be?"}
        to_send = json.dumps(to_send)
        ws.send(to_send)
    if 'done' in message.lower():
        action = 'done'
        to_send = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": "OK, I'm finished training"}
        to_send = json.dumps(to_send)
        ws.send(to_send)
    if action == 'time' and '"type":"message"' in message:
        put_in_db(message)
        to_send = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": "OK, I've got it! What else?"}
        to_send = json.dumps(to_send)
        ws.send(to_send)
    if action == 'training' and 'TIME' in message.upper():
        action = 'time'
    if action == 'training' and 'PIZZA' in message.upper():
        action = 'pizza'
    if action == 'training' and 'GREET' in message.upper():
        action = 'greet'
    if action == 'training' and 'WEATHER' in message.upper():
        action = 'weather'        
    if action == 'training' and 'JOKE' in message.upper():
        action = 'joke'        
def put_in_db(message):
    global action
    conn = sqlite3.connect("name.db")
    c = conn.cursor()
    c.execute("INSERT INTO training_data (txt,action) VALUES (?, ?)", (message, action,))
    conn.commit() # save (commit) the changes\
    
def make_table(database):
    conn = sqlite3.connect("name.db")
    c = conn.cursor() 
    c.execute(database)
    conn.commit()
    
def on_error(ws, error):
    print("in on error")

    print('The error is:', error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    pass
#    def run(*args):
#        print("in run")
#        for i in range(3):
#            message = {"id": 1, "type": "message", "channel": "CNPJBJZ29", "text": "Hello world"}
#            message = json.dumps(message)
#            print(type(message))
#            ws.send(message)
#        time.sleep(1)
#        ws.close()
#        print("thread terminating...")
#    thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    connect_string = f"http://slack.com/api/rtm.connect"
    #caaaurl_string = f"wss://slack.com/api/rtm.start?token={API_TOKEN}&pretty=1"
    #url_string = f"wss://slack.com/api/chat.postMessage?token={API_TOKEN}&channel=project01&text=I'm_Jarvis&as_user=jarvis&pretty=1"
    url_string = requests.get(connect_string, params = {'token': API_TOKEN}).json()['url']
    
    sql_create_training_data_table = """ CREATE TABLE IF NOT EXISTS training_data (
                                         txt text,
                                         action text
                                    ); """
    make_table(sql_create_training_data_table)
    
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(url_string,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    #on_open(ws)
    ws.run_forever()
