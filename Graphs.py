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


def graph_weekday(df, list_sport_type, list_data):
    day_of_week_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday' ]
    palettes = ['pastel', "flare"]
    
    fig = plt.figure(figsize=(7*len(list_data), 5*len(list_sport_type)))
    
    gs = fig.add_gridspec(len(list_sport_type), len(list_data))
    for n, sport_type in enumerate(list_sport_type):
        for m, data in enumerate(list_data):
            ax = fig.add_subplot(gs[n, m])
            sns.violinplot(x='day_of_week', y=data, kind='strip', data=df.loc[df['sport_type'] == sport_type], 
                                order=day_of_week_order, 
                                palette='pastel')
            ax.set_xlabel(sport_type)
            if data in ('distance_km', 'total_elevation_gain'):
                ax.set_ylim(0, None)
    
    fig.tight_layout()
    plt.show()
    

def graph_many(df, list_sport_type, list_data):
    g = sns.PairGrid(df[['sport_type']+list_data].loc[df['sport_type'].isin(list_sport_type)], hue='sport_type', palette='pastel')
    g.map_diag(plt.hist)
    g.map_offdiag(plt.scatter)
    g.add_legend();
    plt.show()


def graph_date(df, list_sport_type, nom_data, chrono, condition):
    df2 = df.loc[(df['sport_type'].isin(list_sport_type))]    

    df2["start_date_local"] = pd.to_datetime(df2["start_date_local"])
    df2['hour_of_day'] = df2['start_date_local'].dt.strftime('%H:00')
    df2['start_date_local'] = df2['start_date_local'].dt.strftime('%Y-%m-%D')

    df2 = df2.sort_values(by=chrono)

    ax = sns.scatterplot(data=df2, x=chrono, y=nom_data)
    ax.set(xlabel=chrono, ylabel=nom_data)
    # ax.set_xlim(df.index[0], df.index[-1])
    ax.tick_params(axis="x", rotation=45)
    plt.show()
    
def distance_week(dfmax, type_act):

    df_sub =  dfmax
    df_sub['start_date_local'] = pd.to_datetime(df_sub['start_date_local'])
    df_sub1 = df_sub.groupby(['type', pd.Grouper(key='start_date_local', freq='W-SUN', label='left')])['distance_km'].sum().reset_index().sort_values('start_date_local')
    df_sub2 = df_sub.groupby(['type', pd.Grouper(key='start_date_local', freq='W-SUN', label='left')])['distance_km'].count().reset_index().sort_values('start_date_local')
    df_sub2.rename(columns={'distance_km':'count'}, inplace=True)
    df_sub = pd.concat([df_sub1, df_sub2['count']], axis=1, join="inner")

    
    idx = pd.date_range('08-01-2022', '29-04-2024', freq='W-SUN')
    for i in idx:
        for stype in ['Run', 'Ride', 'Hike']:
            # print()
            loc = df_sub[(df_sub['start_date_local'] == i) & (df_sub['type'] == stype)]
            if loc.empty:
                new = pd.DataFrame(data={'start_date_local':[i], 'type':[stype], 'distance_km':[0]})#, columns=df_sub.columns)
                df_sub = pd.concat([df_sub, new], ignore_index=True)

    param_graph(df_sub, "start_date_local", "distance_km", "distance per week (Trail+Run) [km]", huea="type",line=True, other='count')


def get_best_5K(df, meas=1000, list_type=['Run']):
    df2 = df.loc[(df['sport_type'].isin(list_type))] 
    df2["start_date_local"] = pd.to_datetime(df2["start_date_local"])
    df2 = df2.sort_values(by="start_date_local")
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
            if dist[-1] >= meas:
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
                    if x > meas + 5:
                        while values[0][-1] - values[0][0] > meas + 5:
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
                print(row["name"], row["sport_type"], f"best {int(meas/1000)}k : ", val5k, rec, mean_heart)
    
    mean_temps = np.mean(results['temps'])
    std_temps = np.std(results['temps'])
    
    # try_smt(noms, wheres)
    
    for key in ['date', 'heartrate', 'where', 'what', 'temps', "elevation", 'delevation']:
        results[key] = [k for k,j in zip(results[key],results['temps']) if j <= mean_temps+2*std_temps]

    results['pace'] = [r/(meas/1000) for r in results['temps']]
    results['speed'] = [(meas/1000)/(r/60) for r in results['temps']]
    
    df = pd.DataFrame.from_dict(results)
    if len(list_type) > 1:
        hue="what"
    else:
        hue=None
    param_graph(df, 'date', "temps", f"durée du meilleur {int(meas/1000)}k", huea=hue)
    # param_graph(df, 'date', "elevation", "dénivelé total de la sortie", huea=hue)
    # param_graph(df, 'date', "delevation", "dénivelé negatif total de la sortie", huea=hue)
    if "Ride" in list_type:
        param_graph(df, 'date', "speed", f"allure du meilleur {int(meas/1000)}k", pace=True, huea=hue)
    else:
        param_graph(df, 'date', "pace", f"allure du meilleur {int(meas/1000)}k", pace=True, huea=hue)

def param_graph(df, timedata, values, label, huea=None, pace=False, heure=False,line=False,other='count'):
    fig, ax = plt.subplots( figsize = (15, 7)) 
    df[timedata] = pd.to_datetime(df[timedata])
    if heure:
        df[values] = pd.to_datetime(df[values])
    
    if line:
        ax2 = ax.twinx()
        ax3 = sns.lineplot(x = timedata, 
                             y = values, 
                             data = df,
                             hue=huea,
                             ax=ax, 
                             markers=True) #'type'
        ax4 = sns.lineplot(x = timedata, 
                             y = other, 
                             data = df,
                             hue=huea,
                             ax=ax2, 
                             markers=True) #'type'
        ax4.lines[0].set_linestyle("--")
        # for idx, row in df.iterrows():
        #     if row[values] > 0 and idx >= 1:
        #         ax1.text(df[timedata][idx], df[values][idx], (int(round(df[values][idx],0)), int(df[other][idx])),
        #                  horizontalalignment='center', color='black',
        #                  bbox=dict(facecolor='white', alpha=0.5), fontsize=8)
    else:
        ax1 = sns.scatterplot(x = timedata, 
                             y = values, 
                             data = df,
                             hue=huea,
                             ax=ax) #'type'
    plt.grid()
    plt.xlabel(label)
    
    # setting customized ticklabels for x axis 
    pos = [f"{y}-{m:02d}-01" for m in range(1,13) for y in range(2022,2025)]
    lab = [ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'June',  
           'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
    lab = [k+f"-{y}" for k in lab for y in range(22,25)]
      
    plt.xticks(pos, lab)
    if heure:
        if 'sunrise' not in df.columns or df['sunrise'][0] == 0:
            for when in ['sunrise', 'sunset', 'dusk', 'dawn']:
                df[when] = 0

            from astral.sun import sun
            from astral import LocationInfo
            from timezonefinder import TimezoneFinder 
            
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
                            date=row[timedata])
                    for when in ['sunrise', 'sunset', 'dusk', 'dawn']:
                        if when in ['sunrise', 'dawn'] and float(s[when].hour) > 12:
                            df.at[idx, when] = str(df[values][0]).split(" ")[0] + f" 00:00:00"
                        elif when in ['sunset', 'dusk'] and float(s[when].hour) < 12:
                            df.at[idx, when] = str(df[values][0]).split(" ")[0] + f" 23:59:59"
                        else:
                            df.at[idx, when] = str(df[values][0]).split(" ")[0] + f" {s[when].hour:02d}:{s[when].minute:02d}:00"
                except:
                    for when in ['sunrise', 'sunset', 'dusk', 'dawn']:
                        if when in ['sunrise', 'dawn']:
                            df.at[idx, when] = str(df[values][0]).split(" ")[0] + f" 00:00:00"
                        elif when in ['sunset', 'dusk']:
                            df.at[idx, when] = str(df[values][0]).split(" ")[0] + f" 23:59:59"

        line = []
        for when in ['sunrise', 'sunset', 'dusk', 'dawn']:
            df[when] = pd.to_datetime(df[when])
            line.append(sns.lineplot(data=df, x=timedata, y=when, color='grey', ax=ax, alpha=.5))
        lines = line[-1].get_lines()

        plt.fill_between(lines[0].get_xdata(),
                         lines[0].get_ydata(),
                         lines[-1].get_ydata(),
                         color='black', alpha=.2 ,zorder=0)
        plt.fill_between(lines[0].get_xdata(),
                         lines[1].get_ydata(),
                         lines[2].get_ydata(),
                         color='black', alpha=.2 ,zorder=0)
        plt.fill_between(lines[0].get_xdata(),
                         lines[-1].get_ydata(),
                         min(lines[0].get_ydata())-0.005,
                         color='black', alpha=.5 ,zorder=0)
        plt.fill_between(lines[0].get_xdata(),
                         lines[2].get_ydata(),
                         max(lines[1].get_ydata())+0.12,
                         color='black', alpha=0.5 ,zorder=0)
        
        pos = [str(df[values][0]).split(" ")[0] + f" {y:02d}:00:00" for y in range(3,24)]
        lab = [f"{y}h" for y in range(3,24)]
        plt.yticks(pos, lab)
        ax.set_ylim(np.mean(lines[0].get_ydata())-0.15, np.mean(lines[0].get_ydata())+0.75)

    if pace:
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_minor_locator(MultipleLocator(0.166667))
        ax.set_ylim(5, 9)
        
    ax.set_xlim(sorted(df[timedata].values)[1], pd.to_datetime('today').normalize())
    ax.tick_params(axis="x", rotation=90)
    ax.grid(which='major', color='#DDDDDD', linewidth=0.8)
    ax.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
    plt.xticks(rotation=45)
    plt.show()
    
def try_smt(noms=['A', 'B'], values=[[30, 50], [10, 80]]):
    new_val = []
    for k in range(100):
        for v in values:
            if v[0] <= k <= v[1]:
                new_val.append(k)
            else:
                new_val.append(np.nan)

    sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
    # Create the data
    g = np.tile(noms, 100)
    df = pd.DataFrame(dict(x=new_val, g=g))
    # Initialize the FacetGrid object
    pal = sns.cubehelix_palette(len(noms), rot=-.25, light=.7)
    g = sns.FacetGrid(df, row="g", hue="g", aspect=15, height=.5, palette=pal, sharey=True)
    # Draw the densities in a few steps
    g.map(sns.kdeplot, "x",
          bw_adjust=.5, clip_on=False,
          fill=True, alpha=1, linewidth=1.5)
    g.map(sns.kdeplot, "x", clip_on=False, color="w", lw=2, bw_adjust=.5)
    # passing color=None to refline() uses the hue mapping
    g.refline(y=0, linewidth=2, linestyle="-", color=None, clip_on=False)
    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, .2, label, fontweight="bold", color=color,
                ha="left", va="center", transform=ax.transAxes)
    
    g.map(label, "x")
    # Set the subplots to overlap
    g.figure.subplots_adjust(hspace=-.25)
    # Remove axes details that don't play well with overlap
    g.set_titles("")
    g.set(yticks=[], ylabel="")
    g.despine(bottom=True, left=True)
    plt.show()
    
def stream_xy(df, x, y):
    for idx,row in df.iterrows():
        if row[x] not in ["", 0, "0"] and row[y] not in ["", 0, "0"]:
            sns.scatterplot(x=st.liststr_to_list(row[x])[:50],
                            y=st.liststr_to_list(row[y])[:50])
    plt.plot()
    
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