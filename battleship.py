#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 18:29:45 2019

@author: sarafergus
"""

boat2length= {'battleship': 4, 'carrier': 5, 'cruiser': 3, 'submarine': 3, 'destroyer':2}
boat2num = {'battleship': 'b', 'carrier': 'c', 'cruiser': 'u', 'submarine': 's', 'destroyer':'d'}
def place_boat(boat, bow, direction, board, boat2length, boat2num):
    letter2num= {'a' : 0, 'b': 1, 'c' : 2, 'd': 3, 'e': 4, 'f':5,'g':6,'h':7,'i':8,'j':9}
    """
    boat: which boat is it?
    bow: where is the front of the boat?
    direction: which way is the boat moving?
    boat2length: dictionary tells how long each boat is
    boat2num: dictionary numbers each boat
    """
    #TODO: incorporate letter2num
    #TODO: change so that Jarvis is picking in a more intelligent way
    try:
        go = True
        bow = parse_coordinate(bow)
        if bow[1] < 0 or bow[0] < 0:
            go = False
            return board, go
        if direction == 'n':
            for i in range(boat2length[boat]):
                if(board[bow[0]+i][bow[1]]) != 0 or bow[0]+i < 0:
                    go = False
            if go == True:
                for j in range(boat2length[boat]):
                    board[bow[0]+j][bow[1]] = boat2num[boat]
        elif direction == 's':
            for i in range(boat2length[boat]):
                if(board[bow[0]-i][bow[1]]) != 0 or bow[0]-i < 0:
                    go = False
            if go == True:
                for j in range(boat2length[boat]):
                    board[bow[0]-j][bow[1]] = boat2num[boat]
        elif direction == 'e':
            for i in range(boat2length[boat]):
                if(board[bow[0]][bow[1]-i]) != 0 or bow[1]-i < 0:
                    go = False
            if go == True:
                for j in range(boat2length[boat]):
                    board[bow[0]][bow[1]-j] = boat2num[boat]
                    
        #default direction is West
        else:
            for i in range(boat2length[boat]):
                if(board[bow[0]][bow[1]+i]) != 0 or bow[1]+i < 0:
                    go = False
            if go == True:
                for j in range(boat2length[boat]):
                    board[bow[0]][bow[1]+j] = boat2num[boat]
    except IndexError as e:
        go = False
    return board, go

def load_gameboard():
    gameboard = []
    for i in range(10):
        temp = []
        for j in range(10):
            temp.append(0)
        gameboard.append(temp)
#    gameboard = [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]
#    gameboard = {'a' : line_a,'b' : line_b,'c' : line_c, 'd' : line_d}
    return gameboard

def fire(location, guess_board,gameboard_opponant):
    location = parse_coordinate(location)
    if gameboard_opponant[location[0]][location[1]] == 'X':
        return("Already fired there, please choose new coordinates.", guess_board, gameboard_opponant)
    elif gameboard_opponant[location[0]][location[1]] == 0:
        gameboard_opponant[location[0]][location[1]] = 'M'
        if guess_board:
            guess_board[location[0]][location[1]] = 'M'
        return("Missed", guess_board,gameboard_opponant)
    else:
        count = 0
        exceptions = 0
        for line in gameboard_opponant:
            for coord in line:
                if str(coord).strip() == gameboard_opponant[location[0]][location[1]].strip():
                    count += 1
                if coord!= 'M' and coord!='X' and coord!= 0:
                    exceptions +=1
                    print(coord, '**********************************8')
        if exceptions == 1:
            return('Winner!', guess_board, gameboard_opponant)
        if count == 1:
            if guess_board:
                guess_board[location[0]][location[1]] = 'X'
                gameboard_opponant[location[0]][location[1]] = 'X'
            return("You have sunk the opponent's ship!", guess_board,gameboard_opponant)
        gameboard_opponant[location[0]][location[1]] = 'X'
        if guess_board:
            guess_board[location[0]][location[1]] = 'X'
        return("Hit!", guess_board,gameboard_opponant)

def start_game():
    b1 = load_gameboard()
    b2 = load_gameboard()
    return b1, b2
    
    
def parse_coordinate(coord):
    c_list = [1,2]
    letter2num= {'a' : 0, 'b': 1, 'c' : 2, 'd': 3, 'e': 4, 'f': 5, 'g' : 6, 'h': 7, 'i' : 8, 'j':9}    
    c_list[0] = letter2num[coord[0]]
    c_list[1] = int(coord[1:]) - 1
    return c_list

