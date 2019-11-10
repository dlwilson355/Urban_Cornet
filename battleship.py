#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:29:45 2019

@author: sarafergus
"""

boat2length= {'battleship': 4, 'carrier': 5, 'cruiser': 3, 'submarine': 3, 'destroyer':2}
boat2num = {'battleship': 'b', 'carrier': 2, 'cruiser': 3, 'submarine': 4, 'destroyer':5}
def place_boat(boat, bow, direction, board, boat2length, boat2num):
    letter2num= {'a' : 0, 'b': 1, 'c' : 2, 'd': 3}
    """
    boat: which boat is it?
    bow: where is the front of the boat?
    direction: which way is the boat moving?
    boat2length: dictionary tells how long each boat is
    boat2num: dictionary numbers each boat
    """
    #TODO: incorporate letter2num
    #TODO: change so that Jarvis is picking in a more intelligent way
    bow = parse_coordinate(bow)
    board[bow[0]][bow[1]] = boat2num[boat]
    go = True
    try:
        #make it so you can't wrap around
        if direction == 'n':
            for i in range(1, boat2length[boat]):
                if(board[bow[0]+i][bow[1]]) != 0:
                    raise IndexError
                else:
                    board[bow[0]+i][bow[1]] = boat2num[boat]
        elif direction == 's':
            for i in range(1, boat2length[boat]):
                if(board[bow[0]-i][bow[1]]) != 0:
                    raise IndexError
                else:
                    board[bow[0]-i][bow[1]] = boat2num[boat] 
        elif direction == 'e':
            for i in range(1, boat2length[boat]):
                if(board[bow[0]][bow[1]+i]) != 0:
                    raise IndexError
                else:
                    board[bow[0]][bow[1]+i] = boat2num[boat] 
                    
        #default direction is West
        else:
            for i in range(1, boat2length[boat]):
                if(board[bow[0]][bow[1]-i]) != 0:
                    raise IndexError
                else:
                    board[bow[0]][bow[1]-i] = boat2num[boat] 
    except IndexError: #except statement for if the boat is going off the grid
        go = False
    #raise an error
    return board, go

def load_gameboard():
    gameboard = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
#    gameboard = {'a' : line_a,'b' : line_b,'c' : line_c, 'd' : line_d}
    return gameboard

def fire(location, guess_board,gameboard_opponant):
    location = parse_coordinate(location)
    if gameboard_opponant[location[0]][location[1]] == -1:
        return("Already fired there, please choose new coordinates.", guess_board, gameboard_opponant)
    elif gameboard_opponant[location[0]][location[1]] == 0:
        gameboard_opponant[location[0]][location[1]] = -1
        if guess_board:
            guess_board[location[0]][location[1]] = 'O'
        return("Missed", guess_board,gameboard_opponant)
    else:
        #im not sure if this is going to work?
        count = 0
        for line in gameboard_opponant:
            for coord in line:
                if coord == gameboard_opponant[location[0]][location[1]]:
                    count += 1
            if count == 0:
                if guess_board:
                    guess_board[location[0]][location[1]] = 'X'
                return("You have sunk the opponent's ship!", guess_board,gameboard_opponant)
        gameboard_opponant[location[0]][location[1]] = -1
        if guess_board:
            guess_board[location[0]][location[1]] = 'X'
        return("Hit!", guess_board,gameboard_opponant)

def start_game():
    b1 = load_gameboard()
    b2 = load_gameboard()
    return b1, b2
    
    
def parse_coordinate(coord):
    letter2num= {'a' : 0, 'b': 1, 'c' : 2, 'd': 3}    
    coord = [x for x in coord]
    coord[0] = letter2num[coord[0]]
    coord[1] = int(coord[1]) - 1
    return coord



    
    
    
    
