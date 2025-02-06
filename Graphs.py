# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:43:38 2025

@author: celine
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
import pandas as pd
import seaborn as sns
import numpy as np


import Settings as st
import ProcessData as prd



class GraphActs():
    def __init__(self, df, timedata="start_date_local"):
        self.df = df
        self.timedata = timedata
        self.df[timedata] = pd.to_datetime(self.df[timedata])
        pass
    
    def weekdays_violin(self, list_data, figsize=(7,5)):
        nb_sport_type = len(self.df['sport_type'].unique())
        fig = plt.figure(figsize=(7*len(list_data), 5*nb_sport_type))
        gs = fig.add_gridspec(nb_sport_type, len(list_data))
        for n,sport_type in enumerate(self.df['sport_type'].unique()):
            for m, data in enumerate(list_data):
                ax = fig.add_subplot(gs[n, m])
                sns.violinplot(x='day_of_week', y=data, data=self.df.loc[self.df['sport_type'] == sport_type], 
                                    order=st.day_of_week_order, 
                                    palette='pastel', cut=0)
                ax.set_xlabel(sport_type)
                if data in ('distance_km', 'total_elevation_gain'):
                    ax.set_ylim(0, None)
        
        fig.tight_layout()
        plt.show()
        
        
    def weekdays_pie(self, list_data, figsize=(7,5)):
        mini_df = self.df[["day_of_week"]+list_data]
        mini_df["day_of_week"] = pd.Categorical(mini_df["day_of_week"], categories = st.day_of_week_order)
        mini_df.sort_values(by = "day_of_week")
        mini_df = mini_df.groupby('day_of_week').sum()
        fig,ax = plt.subplots(1, 3, figsize=(7*len(list_data), 5))
        for m, data in enumerate(list_data): 
            mini_df.plot.pie(y=data, autopct='%.0f%%', ax=ax[m], label=data,
                             colors=st.color_weekday.values(),
                             wedgeprops = {'linewidth':3, 'edgecolor':'white'})
            ax[m].get_legend().remove()
            ax[m].set_title(data)
            ax[m].set_ylabel(None)
            
        fig.legend(st.day_of_week_order, loc=7)
        fig.tight_layout()
        fig.subplots_adjust(right=0.9)
        plt.show()
    
        
    def best_distance(self, distance=1000):
        df_mini = prd.get_best_distance(self.df, distance)
        hue="sport_type"
        
        # self.temporal("temps", f"Duration of best {int(distance/1000)}k [min]", hue=hue, newdf=df_mini)
        self.temporal("pace_best", f"Pace of best {int(distance/1000)}k [min/km]", hue=hue, newdf=df_mini)
            
        # param_graph(df, 'date', "temps", f"durée du meilleur {int(meas/1000)}k", huea=hue)
        # param_graph(df, 'date', "elevation", "dénivelé total de la sortie", huea=hue)
        # param_graph(df, 'date', "delevation", "dénivelé negatif total de la sortie", huea=hue)
        
    
    def beautify_plot(self):
        pass
    
    

    def temporal(self, y, ylabel, hue=None, typegraph="scatterplot", figsize=(15,7), daylight=False, newdf=None):
        cols = [self.timedata, y, "latlng"] if hue is None else [self.timedata, y, hue, "latlng"]
        
        df_mini = self.df[cols] if newdf is None else newdf[cols]
        pace = True if "pace" in y else False 

        # df_mini = df_mini.head(10)
                
        if daylight:
            df_mini[y] = pd.to_datetime(df_mini[y])
        
        fig, ax = plt.subplots(figsize=figsize)
        sns.scatterplot(x=self.timedata, y=y, data=df_mini, hue=hue, ax=ax,
                        palette=st.color_activities, edgecolor="black", linewidth=0.9, zorder=2.5)        
        if daylight:
            df_mini = prd.add_daylight(df_mini, self.timedata, y)
            lines = {}
            for when in ['sunrise', 'sunset', 'dusk', 'dawn']:
                df_mini[when] = pd.to_datetime(df_mini[when])
                l = sns.lineplot(data=df_mini, x=self.timedata, y=when, color='grey', ax=ax, alpha=.5)
                lines[when] = l.get_lines()[-1]
            
            ax.fill_between(df_mini[self.timedata], df_mini["sunrise"], df_mini["dawn"],
                            interpolate=True,
                            color='black', alpha=.2 ,zorder=0)
            ax.fill_between(df_mini[self.timedata], df_mini["sunset"], df_mini["dusk"],
                            interpolate=True,
                            color='black', alpha=.2 ,zorder=0)
            ax.fill_between(df_mini[self.timedata], df_mini["dawn"],  df_mini[y][0].replace(hour=0, minute=0),
                            interpolate=True,
                            color='black', alpha=.5 ,zorder=0)
            ax.fill_between(df_mini[self.timedata], df_mini["dusk"],  df_mini[y][0].replace(hour=23, minute=59),
                            interpolate=True,
                            color='black', alpha=.5 ,zorder=0)    
                

            pos = [str(df_mini[y][0]).split(" ")[0] + f" {h:02d}:00:00" for h in range(0,24)]
            lab = [f"{h}h" for h in range(0,24)]
            plt.yticks(pos, lab)
            ax.set_ylim(df_mini[y][0].replace(hour=0, minute=0), df_mini[y][0].replace(hour=23, minute=59))

        plt.grid()
        pos_major = [f"{y}-{m:02d}-01" for m in [1,7] for y in range(2010,2030)]
        pos_minor = [f"{y}-{m:02d}-01" for m in range(1,13) for y in range(2010,2030)]
        lab_major = [ 'Jan', 'July']
        lab_minor = [ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'June',  
                     'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
        lab_major = [k+f"-{y}" for k in lab_major for y in range(10,30)]
        lab_minor = ["" for k in lab_minor for y in range(10,30)]

        
        plt.xticks(pos_minor, lab_minor, minor=True)
        plt.xticks(pos_major, lab_major, minor=False, rotation=45)
        
        plt.ylabel(ylabel)
        plt.xlabel(None)
        if pace:
            ax.yaxis.set_major_locator(MultipleLocator(1))
            ax.yaxis.set_minor_locator(MultipleLocator(0.166667))
            # ax.set_ylim(5, 9)
        
        ax.set_xlim(sorted(df_mini[self.timedata].values)[1], pd.to_datetime('today').normalize())
        ax.tick_params(axis="x", rotation=90)
        ax.grid(visible=True, which='major', color='#DDDDDD', linewidth=0.8, zorder=-1)
        ax.grid(visible=True, which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5, zorder=-1)
        plt.show()


    # gr.distance_week(dfmax.loc[dfmax['type'] == 'Run'], ["Ride, Run"])
    # gr.graph_weekday(dfmax, ["Run", "TrailRun"], ['distance_km', "average_pace", 'total_elevation_gain'])
    # gr.graph_many(dfmax, ["Run", "TrailRun"], ['type','moving_time_hr','distance_km','total_elevation_gain','average_speed'])
    # gr.stream_xy(dfmax, "distance_y", "heartrate")
    


# def graph_many(df, list_sport_type, list_data):
#     g = sns.PairGrid(df[['sport_type']+list_data].loc[df['sport_type'].isin(list_sport_type)], hue='sport_type', palette='pastel')
#     g.map_diag(plt.hist)
#     g.map_offdiag(plt.scatter)
#     g.add_legend();
#     plt.show()


# def graph_date(df, list_sport_type, nom_data, chrono, condition):
#     df2 = df.loc[(df['sport_type'].isin(list_sport_type))]    

#     df2["start_date_local"] = pd.to_datetime(df2["start_date_local"])
#     df2['hour_of_day'] = df2['start_date_local'].dt.strftime('%H:00')
#     df2['start_date_local'] = df2['start_date_local'].dt.strftime('%Y-%m-%D')

#     df2 = df2.sort_values(by=chrono)

#     ax = sns.scatterplot(data=df2, x=chrono, y=nom_data)
#     ax.set(xlabel=chrono, ylabel=nom_data)
#     # ax.set_xlim(df.index[0], df.index[-1])
#     ax.tick_params(axis="x", rotation=45)
#     plt.show()
    
# def distance_week(dfmax, type_act):

#     df_sub =  dfmax
#     df_sub['start_date_local'] = pd.to_datetime(df_sub['start_date_local'])
#     df_sub1 = df_sub.groupby(['type', pd.Grouper(key='start_date_local', freq='W-SUN', label='left')])['distance_km'].sum().reset_index().sort_values('start_date_local')
#     df_sub2 = df_sub.groupby(['type', pd.Grouper(key='start_date_local', freq='W-SUN', label='left')])['distance_km'].count().reset_index().sort_values('start_date_local')
#     df_sub2.rename(columns={'distance_km':'count'}, inplace=True)
#     df_sub = pd.concat([df_sub1, df_sub2['count']], axis=1, join="inner")

    
#     idx = pd.date_range('08-01-2022', '29-04-2024', freq='W-SUN')
#     for i in idx:
#         for stype in ['Run', 'Ride', 'Hike']:
#             # print()
#             loc = df_sub[(df_sub['start_date_local'] == i) & (df_sub['type'] == stype)]
#             if loc.empty:
#                 new = pd.DataFrame(data={'start_date_local':[i], 'type':[stype], 'distance_km':[0]})#, columns=df_sub.columns)
#                 df_sub = pd.concat([df_sub, new], ignore_index=True)

#     param_graph(df_sub, "start_date_local", "distance_km", "distance per week (Trail+Run) [km]", huea="type",line=True, other='count')


  
    

    
# def try_smt(noms=['A', 'B'], values=[[30, 50], [10, 80]]):
#     new_val = []
#     for k in range(100):
#         for v in values:
#             if v[0] <= k <= v[1]:
#                 new_val.append(k)
#             else:
#                 new_val.append(np.nan)

#     sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
#     # Create the data
#     g = np.tile(noms, 100)
#     df = pd.DataFrame(dict(x=new_val, g=g))
#     # Initialize the FacetGrid object
#     pal = sns.cubehelix_palette(len(noms), rot=-.25, light=.7)
#     g = sns.FacetGrid(df, row="g", hue="g", aspect=15, height=.5, palette=pal, sharey=True)
#     # Draw the densities in a few steps
#     g.map(sns.kdeplot, "x",
#           bw_adjust=.5, clip_on=False,
#           fill=True, alpha=1, linewidth=1.5)
#     g.map(sns.kdeplot, "x", clip_on=False, color="w", lw=2, bw_adjust=.5)
#     # passing color=None to refline() uses the hue mapping
#     g.refline(y=0, linewidth=2, linestyle="-", color=None, clip_on=False)
#     # Define and use a simple function to label the plot in axes coordinates
#     def label(x, color, label):
#         ax = plt.gca()
#         ax.text(0, .2, label, fontweight="bold", color=color,
#                 ha="left", va="center", transform=ax.transAxes)
    
#     g.map(label, "x")
#     # Set the subplots to overlap
#     g.figure.subplots_adjust(hspace=-.25)
#     # Remove axes details that don't play well with overlap
#     g.set_titles("")
#     g.set(yticks=[], ylabel="")
#     g.despine(bottom=True, left=True)
#     plt.show()
    
# def stream_xy(df, x, y):
#     for idx,row in df.iterrows():
#         if row[x] not in ["", 0, "0"] and row[y] not in ["", 0, "0"]:
#             sns.scatterplot(x=st.liststr_to_list(row[x])[:50],
#                             y=st.liststr_to_list(row[y])[:50])
#     plt.plot()
    
