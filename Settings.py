# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:46:16 2025

@author: celine
"""


color_activities = {'Ride':'red', 'Run':'blue', 'Walk':'purple', "Hike":"orange",
                     'BackcountrySki':"black", 'Workout':"grey", 'NordicSki':"pink", 'AlpineSki':"yellow",
                     'IceSkate':"brown", 'WeightTraining':"white", 'EBikeRide':"green", 'Rowing':"brown", 'Sail':"brown",
                     'RockClimbing':"black"}

def listliststr_to_listlist(st):
    return [[float(i.split(", ")[j]) for j in range(len(i.split(", ")))] for i in st[2:-2].split("], [")]

def liststr_to_list(st):
    return [float(i) for i in st[1:-1].split(",")]

