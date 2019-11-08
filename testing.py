#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  4 16:30:14 2019

@author: sarafergus
"""
from csv import reader
from sklearn.model_selection import GridSearchCV
import json
import matplotlib.pyplot as plt
import pickle
import sqlite3
import statistics
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
import glob
import random
import warnings

PATTERN = './data/*-*'
DATABASE_FILE_PATH = "jarvis.db"
BRAIN_SAVE_FILE_PATH = "jarvis_URBANCORNET.pkl"

warnings.filterwarnings("ignore", category=Warning)

#the first half of the functions likely have some duplicate code with jarvis.py

#first three functions read in files. This will have duplicate code
def json_read(filename):
    """This function reads in a json and returns the data in a list."""
    data = []
    f = open(filename)
    for line in f:
        datum = json.loads(line)
        data.append([datum['TXT'], datum['ACTION']])
    return data

def csv_read(filename):
    """This function reads in a csv and returns the data in a list."""
    data = []
    f = open(filename)
    for line in reader(f):
        data.append(line)
    return data
        
def read_file(filename):
    """This function uses the json_read and csv_read functions to read in the
    data from both types of files and returns the data as a list"""
    f = open(filename)
    if f.readline().startswith('{'):
        data = json_read(filename)
    else:
        data = csv_read(filename)
    return data




#exact copy of get_model function from jarvis.py
#further comments on this function in jarvis.py
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


#fits brain
def fit_brain(data):
    """fit brain to data"""
    brain = get_model()
    try: 
        brain.fit(data[0],data[1])
    #file is too small to train brain
    except ValueError:
        brain = None
    return brain



#tests brain
def test_brain(brain, percents, filename, fname):
    """Test brain against data not used for training"""
    #avoid data leak
    if fname == filename:
        pass
    #testing
    else:
        data = read_file(fname)
        correct = 0
        wrong = 0        
        #percent of data which is correct
        #print(39/len(data))
        try:
            for item in data:
                if [item[1]] == brain.predict([item[0]]):
                    correct +=1
                else:
                    wrong +=1
        except:
            #working on some debugging
            print(item)
            print(filename)
            print(fname)
            #print(fname[-10:], ': ', correct,' correct', wrong, ' wrong.', round(correct/(wrong+ correct),2)*100, 'percent')        
        percents.append(correct/(wrong+correct))
    return percents



#Get the information about our DB, essentially same as in jarvis.py
def DB_data():
    """Get data from our database"""
    connection = sqlite3.connect(DATABASE_FILE_PATH)
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
    print(len(x))
    return x, y



#plotting function
def plot_percents(percents):
    """Plot accuracy of various brains"""
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
 

#gets boolean accuracy of brain by average percent of each file
def compare_accuracy():
    """Determine accuracy of brain"""
    percents = []
    all_percents = []
    db_accuracy = []
    i = 0
    for filename in get_filenames():
        print(i)
        i += 1
        data = read_file(filename)
        data = list(zip(*data))
        brain = fit_brain(data)
        if not brain:
            #datafile is too small for training
            continue
        for fname in get_filenames():
            percents = test_brain(brain, percents, [filename], fname)
        all_percents.append(sum(percents)/len(percents))
        percents = []
        i += 1
    plot_percents(all_percents)
    
    # get info for our data
    db_brain = fit_brain(DB_data())
    db_accuracy = []
    for fname in get_filenames():
        db_accuracy = test_brain(db_brain, db_accuracy, ['none'], fname)
    print("Our Accuracy: ", sum(db_accuracy)/len(db_accuracy))



#reads in from data folder
def get_filenames():
    """Get external data files"""
    filenames = []
    for filename in glob.glob(PATTERN):
        filenames.append(filename)
    return filenames



#create incrimentally larger traing sets, train brain, test brains accuracy. Plot results.
def compare_sizes():
    """Grow size of training data and test for accuracy on each size"""
    data = DB_data()
    filenames = get_filenames()
    sizes = []
    data_names = []
    percent = []
    percents = []
    
    #grow size of training data
    while len(data[0]) < 1000:
        brain = fit_brain(data)
        for fname in get_filenames():
            percent = test_brain(brain, percent, data_names, fname)
        percents.append(sum(percent)/len(percent))
        sizes.append(len(data[0]))
        next_file = random.choice(filenames)
        data_names.append(next_file)
        filenames.remove(next_file)
        next_file = list(zip(*(read_file(next_file))))
        data = [data[0] + list(next_file[0]), data[1] + list(next_file[1])]
    
    #plot    
    plt.scatter(sizes, percents)
    plt.title("Accuracy of Brain Based on Size of Training Data")
    plt.xlabel("Items in Training Data")
    plt.ylabel("Accuracy (percent as decimal)")
    plt.show()


#determine sizes and breakdowns of external data    
def EDA():
    sizes = []
    types = {'PIZZA': 0, 'GREET':0,'JOKE':0,'WEATHER':0, 'TIME':0}
    filenames= get_filenames()
    for f in filenames:
        data = read_file(f)
        sizes.append(len(data))
        data = list(zip(*data))
        for item in data[1]:
            for jtem in types.keys():
                if item == jtem:
                    types[jtem] += 1
    sizes.sort()
    #ignore particularly large files (for visual clarity)
    plt.hist(sizes[:-4], bins = 'auto')
    print(sizes[-4:])
    plt.title("Data File Sizes")
    plt.xlabel("Number of Phrases")
    plt.ylabel("Count")
    plt.show()
    #plot types
    plt.bar([1,2,3,4,5], list(types.values()))
    plt.xticks([1,2,3,4,5], ('PIZZA','GREET','JOKE','WEATHER','TIME'))
    plt.title("Types of Phrases")
    plt.xlabel('Action')
    plt.ylabel('Count')
    plt.show()




########################### calling functions #################################
    
#check performance on bad data
#percents = []  
#brain = pickle.load(open(BRAIN_SAVE_FILE_PATH, 'rb'))
#for filename in get_filenames():  
#    percents = test_brain(brain, percents, filename, 'bad_file.txt')
#print(sum(percents)/len(percents))

#train on bad data
#percents = []
#data = read_file('bad_file.txt')
#print(data)
#brain = fit_brain(data)
#for filename in get_filenames():
#    percents = test_brain(brain, percents, 'bad_file.txt', filename)
#print(sum(percents)/len(percents))


#DB_data()        
#EDA()    
compare_accuracy()
#compare_sizes()
