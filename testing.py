#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 16:30:14 2019

@author: sarafergus
"""
import pickle
from csv import reader
import json
import glob


brain = pickle.load(open("jarvis_URBANCORNET.pk1", 'rb'))
result = brain.predict (["Hello funny roboooot!"])
print(result)

#Test accuracy of brain based on our data
def j_read(filename):
    data = []
    f = open(filename)
    for line in f:
        datum = json.loads(line)
        data.append([datum['TXT'], datum['ACTION']])
    return data

def csv_read(filename):
    data = []
    f = open(filename)
    for line in reader(f):
        data.append(line)
    return data
        
def read_file(filename):
    f = open(filename)
    if '{' in f.readline():
        data = j_read(filename)
    else:
        data = csv_read(filename)
    return data

percents = []
for filename in glob.glob('*-*'):
    if 'BAD' in filename:
        pass
    else:
        data = read_file(filename)
        correct = 0
        wrong = 0
        for item in data:
            if [item[1]] == brain.predict([item[0]]):
                correct +=1
            else:
                wrong +=1 
        print(filename, ': ', correct,' correct', wrong, ' wrong.', round(correct/(wrong+ correct),2)*100, 'percent')        
        percents.append(correct/(wrong+correct))
        
print(sum(percents)/len(percents))            
