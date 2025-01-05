# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:47:12 2025

@author: celine
"""

import folium
import Settings as st
import ProcessData as pr

def get_map(dfmax, name):
    """ Write a html file containing a map of all activities.
    
    Parameters
    ----------
    dfmax : Dataframe with both activities and stream data
    name : name to be used for the output file

    Returns: None.

    """
    # plot all activities on map
    resolution, width, height = 75, 6, 6.5
    
    def centroid(polylines):
        """ return the mean coordinates of all activities with spatial data """
        x, y = [], []
        for idx, polyline in polylines.items():
            if polyline not in ["", 0, "0"]:
                for coord in st.listliststr_to_listlist(polyline):
                    x.append(coord[0])
                    y.append(coord[1])
        return [(min(x)+max(x))/2, (min(y)+max(y))/2]


    m = folium.Map(location=centroid(dfmax['latlng']), zoom_start=4)
    elevation_profile = pr.get_profiles(dfmax,
                                        x_axe={"name":"Distance", "col_name":"distance_y"},
                                        y_axe={"name":"Elevation", "col_name":"altitude"})
    speed_profile = pr.get_profiles(dfmax,
                                    x_axe={"name":"Distance", "col_name":"distance_y"},
                                    y_axe={"name":"Vitesse", "col_name":"velocity_smooth"})

    for idx, row in dfmax.iterrows():
        if row['latlng'] not in ["", 0, "0"]: # Activities with no spatial data are ignored
            folium.PolyLine(st.listliststr_to_listlist(row['latlng']),
                            color=st.color_activities[row['type']]).add_to(m)
            halfway_coord = st.listliststr_to_listlist(row['latlng'])[int(len(st.listliststr_to_listlist(row['latlng']))/2)]# popup text
            html = """
            <h3>{}</h3>
                <p>
                    <code>
                    Date : {} <br>
                    Time : {}
                    </code>
                </p>
            <h4>{}</h4>
                <p> 
                    <code>
                        Distance&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp: {:.2f} km <br>
                        Elevation Gain&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp: {:.0f} m <br>
                        Moving Time&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp: {:.0f}h{:.0f} min<br>
                        Average Speed&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp: {:.2f} km/h (maximum: {:.2f} km/h) <br>
                        Average Heart Rate&nbsp;&nbsp: {:.0f} bpm (maximum: {:.0f} bpm) <br>
                    </code>
                </p>
            <img src="data:image/png;base64,{}"> <br>
            <img src="data:image/png;base64,{}"> 
            """.format(
                row['name'], 
                row["start_date_local"].split(" ")[0], 
                row["hour_of_day"],  
                row['type'], 
                row['distance_km'], 
                row['total_elevation_gain'], 
                int(row['moving_time_hr']),
                (row['moving_time_hr']% 1)*60, 
                row['average_speed_kmh'],
                row['max_speed_kmh'], 
                float(row['average_heartrate']),
                float(row['max_heartrate']),
                elevation_profile[row['id']],
                speed_profile[row['id']], 
            )
            
            # add marker to map
            iframe = folium.IFrame(html,
                                   width=(width*resolution)+20,
                                   height=(height*resolution)+20)

            popup = folium.Popup(iframe, max_width=2650)
            icon = folium.Icon(color=st.color_activities[row['type']], icon='info-sign')
            marker = folium.Marker(location=halfway_coord, popup=popup, icon=icon)
            marker.add_to(m)

    print(f'mymap_{name}.html')
    m.save(f'mymap_{name}.html')