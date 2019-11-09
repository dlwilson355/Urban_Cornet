#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:29:45 2019

@author: sarafergus
"""
letter2num= {'a' : 0, 'b': 1}
boat2length= {'battleship': 4, 'carrier': 5, 'cruiser': 3, 'submarine': 3, 'destroyer':2}
boat2num = {'battleship': 1, 'carrier': 2, 'cruiser': 3, 'submarine': 4, 'destroyer':5}
def place_boat(boat, bow, direction, board, boat2length, boat2num):
    """
    boat: which boat is it?
    bow: where is the front of the boat?
    direction: which way is the boat moving?
    boat2length: dictionary tells how long each boat is
    boat2num: dictionary numbers each boat
    """
    board[bow[0]][bow[1]] = boat2num[boat]
    go = True
    try:
        if direction == 'north':
            for i in range(1, boat2length[boat]):
                board[bow[0]][bow[1]] = boat2num[boat]
        elif direction == 'south':
            for i in range(1, boat2length[boat]):
                board[bow[0]][bow[1]] = boat2num[boat] 
        elif direction == 'east':
            for i in range(1, boat2length[boat]):
                board[bow[0]-i][bow[1]] = boat2num[boat] 
        else:
            for i in range(1, boat2length[boat]):
                board[bow[0]+i][bow[1]] = boat2num[boat] 
    except: #except statement for if the boat is going off the grid
        print('You cannot place your boat there. Try again')
        go = False
    #raise an error
    return board, go

def load_gameboard():
    line_a = [0,0,0,0]
    line_b = [0,0,0,0]
    line_c = [0,0,0,0]
    line_d = [0,0,0,0]
    gameboard = {a : line_a,b : line_b,c : line_c, d : line_d}
    return gameboard

def fire(location,gameboard_opponant):
    if gameboard_opponant[location[0]][location[1]] == -1:
        print("Already fired there, please choose new coordinates.")
    elif gameboard_opponant[location[0]][location[1]] == 0:
        gameboard_opponant[location[0]][location[1]] = -1
        print("Missed")
    else:
        print("Hit")
        count = 0
        for line in gameboard_opponant:
            for coord in line:
                if coord == gameboard_opponant[location[0]][location[1]]:
                    count += 1
            if count == 0:
                print("You have sunk the opponant's ship!")
        gameboard_opponant[location[0]][location[1]] = -1


    
    
    
    