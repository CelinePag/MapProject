# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:50:36 2025

@author: celine
"""

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