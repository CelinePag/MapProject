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
    df2 = dfmax.sort_values(by="start_date_local")
    noms = []
    wheres = []
    results = {'temps':[], "date":[], "heartrate":[], "where":[], "what":[], "elevation":[], "delevation":[]}
    for idx,row in df2.iterrows():
        if row["distance_y"] not in (0,'0') and row["time"] not in (0,'0'):
            dist = [float(k) for k in row["distance_y"][1:-1].split(",")]
            tim = [float(k) for k in row["time"][1:-1].split(",")]
            elevation = [float(k) for k in row["altitude"][1:-1].split(",")]
            if row["heartrate"] not in (0,'0'):
                heart = [float(k) for k in row["heartrate"][1:-1].split(",")]
            else:
                heart = len(tim)*[0]
            if dist[-1] >= distanceK:
                val5k = 500000
                rec = [0,0]
                elev_tot = 0
                delev_tot = 0
                values = [[0],[0],[0]]
                mean_heart = 0
                elev_p = elevation[0]
                for x,t,h,e in zip(dist, tim, heart,elevation):
                    if e > elev_p:
                        elev_tot += e - elev_p
                    else:
                        delev_tot += elev_p - e
                    elev_p = e

                    values[0].append(float(x))
                    values[1].append(float(t))
                    values[2].append(float(h))
                    if x > distanceK + 5:
                        while values[0][-1] - values[0][0] > distanceK + 5:
                            values[0] = values[0][1:]
                            values[1] = values[1][1:]
                            values[2] = values[2][1:]
                        test5k = (values[1][-1] - values[1][0])/60
                        if test5k < val5k:
                            val5k = test5k
                            rec = [values[0][0], values[0][-1]]
                            mean_heart = int(np.mean(values[2]))
                noms.append(row["name"])
                wheres.append([r*100/row['distance_x'] for r in rec])
                
                results['what'].append(row["sport_type"])
                results['elevation'].append(elev_tot)
                results['delevation'].append(delev_tot)
                results['temps'].append(val5k)
                results['heartrate'].append(mean_heart)
                results['where'].append(rec)
                results['date'].append(row["start_date_local"])
                print(row["name"], row["sport_type"], f"best {int(distanceK/1000)}k : ", val5k, rec, mean_heart)
    
    mean_temps = np.mean(results['temps'])
    std_temps = np.std(results['temps'])
    
    # try_smt(noms, wheres)
    
    for key in ['date', 'heartrate', 'where', 'what', 'temps', "elevation", 'delevation']:
        results[key] = [k for k,j in zip(results[key],results['temps']) if j <= mean_temps+2*std_temps]

    results['pace'] = [r/(distanceK/1000) for r in results['temps']]
    results['speed'] = [(distanceK/1000)/(r/60) for r in results['temps']]
    return results



def get_profiles(dfmax, x_axe, y_axe):
    profile = dict()
    for idx, row in dfmax.iterrows():
        # figure
        fig, ax = plt.subplots(figsize=(6, 2))
        if row[x_axe["col_name"]] not in ["", 0, "0"] and row[y_axe["col_name"]] not in ["", 0, "0"]:
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
            profile[row['id']] = base64.b64encode(open(png, 'rb').read()).decode()
         
            # delete file
            os.remove(png)
    return profile

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