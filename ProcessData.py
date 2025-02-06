# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:50:36 2025

@author: celine
"""

from astral.sun import sun
from astral import LocationInfo
from timezonefinder import TimezoneFinder 
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import base64
import os
import Settings as st


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def get_vit_ascen(temps, altitude):
    vit = []
    
    for k in range(len(temps)-1):
        vit_k = (altitude[k+1]-altitude[k])/(temps[k+1]-temps[k]) #m/s
        vit_k = max(-2000, min(2000,vit_k *3600))
        vit.append(vit_k)
    vit.append(vit_k)
    s = temps[-1]/len(temps)
    vit = moving_average(vit, int(900/s))
    return vit


def add_daylight(df, x, y):
    periods = ['sunrise', 'sunset', 'dusk', 'dawn']
    
    for when in periods:
        df[when] = 0

    for idx, row in df.iterrows():
        try:
            lat = float(row["latlng"][2:23].split(",")[0])
            long = float(row["latlng" ][2:23].split(",")[1][1:-1])
        except:
            lat = None
            long = None
        timezone = 'Europe/Paris'
        try:
            timezone = TimezoneFinder().timezone_at(lng=long, lat=lat)
            s = sun(LocationInfo('name', 'region', timezone,
                                 lat, long).observer,
                    date=row[x])
            for when in periods:
                if when in ['sunrise', 'dawn'] and float(s[when].hour) > 12:
                    df.at[idx, when] = str(df[y][0]).split(" ")[0] + f" 00:00:00"
                elif when in ['sunset', 'dusk'] and float(s[when].hour) < 12:
                    df.at[idx, when] = str(df[y][0]).split(" ")[0] + f" 23:59:59"
                else:
                    df.at[idx, when] = str(df[y][0]).split(" ")[0] + f" {s[when].hour:02d}:{s[when].minute:02d}:00"
        except: # too far north or south and no night for example
            for when in periods:
                if when in ['sunrise', 'dawn']:
                    df.at[idx, when] = str(df[y][0]).split(" ")[0] + f" 00:00:00"
                elif when in ['sunset', 'dusk']:
                    df.at[idx, when] = str(df[y][0]).split(" ")[0] + f" 23:59:59"

    for when in periods:
        df[when] = pd.to_datetime(df[when])
    return df


def get_best_distance(dfmax, distanceK):
    df2 = dfmax.sort_values(by="start_date_local")[["id", "name", "distance_x", "sport_type",
                                                    "start_date_local",
                                                    "distance_y", "time",
                                                    "heartrate", "altitude",
                                                    "latlng"]]
    
    df2 = df2[df2["distance_x"] >= distanceK] # only take activities longer than distanceK
    df2["elevation_best"] = 0
    df2["delevation_best"] = 0
    df2["heartrate_best"] = 0
    df2["pace_best"] = 0
    df2["speed_best"] = 0
    df2["start_best"] = 0
    df2["end_best"] = 0
    df2["time_best"] = 0

    for idx,row in df2.iterrows():
        if row["distance_y"] not in (0,'0',np.nan, None) and row["time"] not in (0,'0',np.nan, None):

            dist = [float(k) for k in row["distance_y"][1:-1].split(",")]
            tim = [float(k) for k in row["time"][1:-1].split(",")]
            try:
                heart = [float(k) for k in row["heartrate"][1:-1].split(",")]
            except (ValueError, TypeError):
                heart = len(dist)*[0]
            try:
                alt = [float(k) for k in row["altitude"][1:-1].split(",")]
            except (ValueError, TypeError):
                alt = len(dist)*[0]
            
            
            best_time_K = 500000
            memory = {"x":[0], "t":[0]}
            x_best = [0,0]
            for x,t in zip(dist, tim):
                memory["x"].append(float(x))
                memory["t"].append(float(t))
                if x > distanceK + 5:
                    while memory["x"][-1] - memory["x"][0] > distanceK + 5:
                        memory["x"] = memory["x"][1:]
                        memory["t"] = memory["t"][1:]
                    time_K = (memory["t"][-1] - memory["t"][0])/60
                    if time_K < best_time_K:
                        best_time_K = time_K
                        x_best = [memory["x"][0], memory["x"][-1]]

            i_deb, i_fin = dist.index(x_best[0]), dist.index(x_best[-1])
            elevation_best = 0
            delevation_best = 0
            elev_ref = alt[i_deb]
            for e in alt[i_deb: i_fin+1]:
                if e > elev_ref:
                    elevation_best += e - elev_ref
                else:
                    delevation_best += elev_ref - e
                elev_ref = e

            df2.at[idx, "time_best"] = best_time_K
            df2.at[idx, "elevation_best"] = elevation_best
            df2.at[idx, "delevation_best"] = delevation_best
            df2.at[idx, "heartrate_best"] = int(np.mean(heart[i_deb:i_fin+1]))
            df2.at[idx, "pace_best"] = best_time_K/(distanceK/1000)
            df2.at[idx, "speed_best"] = (distanceK/1000)/(best_time_K/60)
            df2.at[idx, "start_best"] = x_best[0]
            df2.at[idx, "end_best"] = x_best[-1]
    
    # remove outliers
    mean_duration = df2['time_best'].mean()
    std_duration = df2['time_best'].std()
    df2["z_score"] = (df2['time_best']-mean_duration)/std_duration
    threshold = 3
    df2 = df2[df2["z_score"] <= threshold]

    return df2



def get_all_profiles(dfmax, x_axe, y_axe):
    profile = dict()
    for idx, row in dfmax.iterrows():
        # figure
        profile[row['id']] = get_profile_id(row, x_axe, y_axe)
    return profile

def get_profile_id(row, x_axe, y_axe):
    fig, ax = plt.subplots(figsize=(6, 2))
    if row[x_axe["col_name"]] not in ["", 0, "0", np.nan] and row[y_axe["col_name"]] not in ["", 0, "0", np.nan]:
        mini_df = pd.DataFrame({x_axe["name"]:st.liststr_to_list(row[x_axe["col_name"]]),
                                y_axe["name"]:st.liststr_to_list(row[y_axe["col_name"]])})
        
        if x_axe["name"] not in ["distance_y", "Elevation"]:
            mini_df[x_axe["name"]] = mini_df[x_axe["name"]].rolling(20).mean()
        if y_axe["name"] not in ["distance_y", "Elevation"]:
            mini_df[y_axe["name"]] = mini_df[y_axe["name"]].rolling(20).mean()
        if y_axe["name"] == "Vitesse":
            mini_df[y_axe["name"]] = mini_df[y_axe["name"]] * 3.6
        if x_axe["name"] == "Distance":
            mini_df[x_axe["name"]] = mini_df[x_axe["name"]]/1000
        ax = mini_df.plot(x=x_axe["name"], y=y_axe["name"], ax=ax, 
                            color=st.color_activities[row['type']],
                            legend=False, )
        
        ax.set_ylabel(y_axe["name"])
        ax.set_xlabel(x_axe["name"])
        # ax.axes.xaxis.set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        png = 'elevation_profile_{}.png'.format(row['id'])
        fig.savefig(png, dpi=75)
        plt.close()
        # read png file
        profile_id = base64.b64encode(open(png, 'rb').read()).decode()
        # delete file
        os.remove(png)
    return profile_id

def get_VAP(speed, grade):
    func = lambda x: 0.0015*x*x + 0.0279*x + 1
    vap = []
    pace = []
    adjust = []
    # print(temps)
    for k in range(len(speed)-1):
        
        pace_k = 1/(max(0.01,speed[k])*1000/60)
        vaps = pace_k/func(grade[k])
        vap.append(vaps)
        pace.append(pace_k)
        adjust.append(func(grade[k]))
    
    plt.plot(grade)
    plt.show()
    plt.plot(adjust)
    plt.show()
    vap.append(vaps)
    pace.append(pace_k)
    return vap, pace