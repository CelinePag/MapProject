# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:46:16 2025

@author: celine
"""



color_activities = {'Ride':'#18a81a',
                    'EBikeRide':"#075208",
                    'Run':'#c92020',
                    'Walk':'#b8a109',
                    "Hike":"#e88e17",
                     'BackcountrySki':"#070b52",
                     'NordicSki':"#087c9c",
                     'AlpineSki':"#1702ba",
                     'IceSkate':"#7209b8",
                     'Workout':"grey",
                     'WeightTraining':"white",
                     'Rowing':"#d9308a", 
                     'Sail':"#d9308a",
                     'RockClimbing':"black"}

day_of_week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday' ]
color_weekday = {'Monday':"#a83a32", 'Tuesday':"#078743", 'Wednesday':"#737373", 'Thursday':"#d96309", 'Friday':"#144a2e", 'Saturday':"#566bbf", 'Sunday':"#a562bd" }

typact_run = ['Run', 'TrailRun']
typact_foot = typact_run + ['Walk', "Hike"]
typact_winter = ['BackcountrySki', 'NordicSki', 'AlpineSki', 'IceSkate']
typact_sport = typact_foot + ['BackcountrySki', 'NordicSki']

def listliststr_to_listlist(st):
    return [[float(i.split(", ")[j]) for j in range(len(i.split(", ")))] for i in st[2:-2].split("], [")]

def liststr_to_list(st):
    return [float(i) for i in st[1:-1].split(",")]

