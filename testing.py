#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 16:30:14 2019

@author: sarafergus
"""
import pickle
from csv import reader
import json
import websocket
import matplotlib.pyplot as plt
import sqlite3
import statistics
import json
import sklearn
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, train_test_split, cross_validate
import pickle
import os
import glob
import random

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

def get_model():
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

    model = GridSearchCV(pipeline, params, cv=10, iid=False, n_jobs=-1)

    return model

def fit_brain(data):
    brain = get_model()
    try: 
        brain.fit(data[0],data[1])
    except Exception as e:
        brain = None
    return brain

def test_brain(brain, percents, filename, fname):
    #these two were kept as bad files
    if fname == './data/11ebcd49-428a-1c22-d5fd-b76a19fbeb1d':
        pass
    elif fname == './data/12e0c8b2-bad6-40fb-1948-8dec4f65d4d9':
        pass
    #avoid data leak
    elif fname in filename:
        pass
    #testing
    else:
        data = read_file(fname)
        correct = 0
        wrong = 0
        for item in data:
            if [item[1]] == brain.predict([item[0]]):
                correct +=1
            else:
                wrong +=1 
#        print(fname[-10:], ': ', correct,' correct', wrong, ' wrong.', round(correct/(wrong+ correct),2)*100, 'percent')        
        percents.append(correct/(wrong+correct))  
    return percents

def our_data():
    connection = sqlite3.connect('jarvis.db')
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS training_data "
                       "(txt text, action text)")
    # load the data from the database
    cursor.execute("SELECT * from training_data")
    data = cursor.fetchall()

    # sort the messages and labels
    x, y = [], []
    for row in data:
        x.append(row[0])
        y.append(row[1])

    return x, y

def plot_percents(percents):
    fig, ax = plt.subplots()
    mu = statistics.mean(percents)
    sigma = (statistics.stdev(percents))
    textstr = '\n'.join((
            r'$\mu=%.2f$' % (mu, ),
            r'$\sigma=%.2f$' % (sigma, )))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
    verticalalignment='top', bbox=props)
    ax.hist(percents, bins = 'auto')
    plt.title('Accuracy of Brain Trained on Single Data File')
    plt.ylabel('Count')
    plt.xlabel('Percent as Decimal')
    plt.show()
 

def compare_accuracy():
    percents = []
    o_accuracy = []
    for filename in glob.glob('./data/s*-*'):
        data = read_file(filename)
        data = list(zip(*data))
        brain = fit_brain(data)
        if not brain:
            #datafile is too small for training
            continue
        for fname in glob.glob('./data/*-*'):
            percents = test_brain(brain, percents, [filename], fname)
    plot_percents(percents)
    # get info for our data
    our_brain = fit_brain(our_data())
    o_accuracy = []
    for fname in glob.glob('./data/*-*'):
        o_accuracy = test_brain(our_brain, o_accuracy, ['none'], fname)
    print("Our Accuracy: ", sum(o_accuracy)/len(o_accuracy))

def get_filenames():
    filenames = []
    for filename in glob.glob('./data/*-*'):
        if fname == './data/11ebcd49-428a-1c22-d5fd-b76a19fbeb1d':
            pass
        elif fname == './data/12e0c8b2-bad6-40fb-1948-8dec4f65d4d9':
            pass
        else:
            filenames.append(filename)
    return filenames

def compare_sizes():
    data = our_data()
    filenames = get_filenames()
    sizes = []
    data_names = []
    percent = []
    percents = []
    while len(data[0]) < 1000:
        brain = fit_brain(data)
        for fname in glob.glob('./data/*-*'):
            percent = test_brain(brain, percent, data_names, fname)
        percents.append(sum(percent)/len(percent))
        sizes.append(len(data[0]))
        next_file = random.choice(filenames)
        data_names.append(next_file)
        filenames.remove(next_file)
        next_file = list(zip(*(read_file(next_file))))
        data = [data[0] + list(next_file[0]), data[1] + list(next_file[1])]
        print(len(data[0]))
    plt.scatter(sizes, percents)
    plt.title("Accuracy of Brain Based on Size of Training Data")
    plt.xlabel("Items in Training Data")
    plt.ylabel("Accuracy (percent as decimal)")
    plt.show()
    

compare_accuracy()
compare_sizes()
