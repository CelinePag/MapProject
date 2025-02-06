# -*- coding: utf-8 -*-
"""
Created on Sun Mar 17 09:55:42 2024

@author: celine
"""

import pandas as pd
import ClientHandler as ch
import Graphs as gr
import Maps as mp
import Settings as st
pd.options.display.max_columns = None


# TODO

if __name__ == "__main__":
    who = "celine"
    Cli = ch.ClientStrava(who)
    Act = ch.Activities(Cli.client, Cli.nom) # 1 request
    
    runs = Act.df.loc[Act.df['sport_type'] == 'Run']
    hikes = Act.df.loc[Act.df['sport_type'] == 'Hike']
    trails = Act.df.loc[Act.df['sport_type'] == 'TrailRun']
    hikes_run = pd.concat([runs, hikes, trails])
    bikes = Act.df.loc[Act.df['type'] == 'Ride']
    otherActi = Act.df.loc[(Act.df['type'] != 'Run') & (Act.df['type'] != 'Hike') & (Act.df['type'] != 'TrailRun') & (Act.df['type'] != 'Ride')]

    if True:
        print("récupération nouvelles activités...")
        Act.init_csv_streams(runs, nb=99, name="run")
        Act.init_csv_streams(hikes, nb=99, name="hikes")
        Act.init_csv_streams(trails, nb=99, name="trail")
        Act.init_csv_streams(bikes, nb=99, name="bike")
        Act.init_csv_streams(otherActi, nb=99, name="other")

    dfs_run = pd.read_csv(f'{ch.PATH_CSV}\strava_activities_stream_{Cli.nom}_run.csv').fillna(0)
    dfs_hikes = pd.read_csv(f'{ch.PATH_CSV}\strava_activities_stream_{Cli.nom}_hikes.csv').fillna(0)
    dfs_trail = pd.read_csv(f'{ch.PATH_CSV}\strava_activities_stream_{Cli.nom}_trail.csv').fillna(0)
    dfs_bike = pd.read_csv(f'{ch.PATH_CSV}\strava_activities_stream_{Cli.nom}_bike.csv').fillna(0)
    dfs_other = pd.read_csv(f'{ch.PATH_CSV}\strava_activities_stream_{Cli.nom}_other.csv').fillna(0)

    dfs = pd.concat([dfs_run, dfs_hikes, dfs_trail, dfs_bike, dfs_other])   
    dfmax = pd.merge(Act.df, dfs, on='id', how="outer")#left_on='Unnamed: 0', right_on='team_name')
        
    # ----------- Html map
    mp.get_map(dfmax, Cli.nom)
    
    # ----------- various graphs
    # gr.distance_week(dfmax.loc[dfmax['type'] == 'Run'], ["Ride, Run"])
    # gr.graph_many(dfmax, ["Run", "TrailRun"], ['type','moving_time_hr','distance_km','total_elevation_gain','average_speed'])
    # gr.stream_xy(dfmax, "distance_y", "heartrate")
    
    # graphs = gr.GraphActs(dfmax[dfmax["sport_type"].isin(st.typact_sport)])
    # graphs.temporal("total_elevation_gain", "Total elevation gain [m]", hue="sport_type")
    # graphs.temporal("distance_km", "Distance [km]", hue="sport_type")
    # graphs.temporal("elev_high", "Max altitude reached [m]", hue="sport_type")
    # graphs.temporal("moving_time_hr", "Moving time [hour]", hue="sport_type")
    
    # graphs.temporal("hour_of_day", "Start of Activity", hue="sport_type", daylight=True)
    
    # graphs.weekdays_violin(['distance_km', "average_speed_kmh", 'total_elevation_gain'])
    # graphs.weekdays_pie(['distance_km', 'total_elevation_gain', "moving_time_hr"])


    # graphs_foot = gr.GraphActs(dfmax[dfmax["sport_type"].isin(st.typact_run)])
    # graphs_foot.best_distance(distance=5000)

    
