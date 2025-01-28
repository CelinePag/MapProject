# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:47:12 2025

@author: celine
"""

import folium
import Settings as st
import ProcessData as pr
from folium.plugins import HeatMap
from folium.plugins import OverlappingMarkerSpiderfier
from folium.map import Marker, Template, Layer


# TODO add option to show/hide polyline depending on the type of the activity

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

    groups = {}
    for type_activity in dfmax.type.unique():
        groups[type_activity] = folium.FeatureGroup(name=type_activity).add_to(m)
    
    # groups["marker"] = folium.FeatureGroup(name="marker").add_to(m)
    
    for idx, row in dfmax.iterrows():
        if row['latlng'] not in ["", 0, "0"]: # Activities with no spatial data are ignored
            activity = row['type']
            groups[activity].add_child(folium.PolyLine(st.listliststr_to_listlist(row['latlng']),
                                                       color=st.color_activities[row['type']],
                                                       Highlight= True,
                                                       show=True,
                                                       overlay=True,
                                                       tooltip=row['name'],
                                                       pathCoords=st.listliststr_to_listlist(row['latlng'])))
            # folium.PolyLine(st.listliststr_to_listlist(row['latlng']),
            #                 color=st.color_activities[row['type']],
            #                 Highlight= True,
            #                 name = "Wills",
            #                 show=True,
            #                 overlay=True,).add_to(m)
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
            icon = folium.Icon(color='black',icon_color=st.color_activities[row['type']], icon='info-sign')
            marker = folium.Marker(location=halfway_coord,
                                   popup=popup,
                                   icon=icon,
                                   tooltip=row['name'],
                                   pathCoords=st.listliststr_to_listlist(row['latlng']))
            groups[activity].add_child(marker)
            # groups["marker"].add_child(marker)

            # marker.add_to(m)

    # Add the OverlappingMarkerSpiderfier plugin
    oms = OverlappingMarkerSpiderfier(
        keep_spiderfied=True,  # Markers remain spiderfied after clicking
        nearby_distance=20,  # Distance for clustering markers in pixel
        circle_spiral_switchover=10,  # Threshold for switching between circle and spiral
        leg_weight=2.0  # Line thickness for spider legs
        )
    oms.add_to(m)
    
    # Add legend
    m.get_root().add_child(get_legend())
    
    # Add dark and light mode. 
    folium.TileLayer('cartodbdark_matter',name="dark mode",control=True).add_to(m)
    folium.TileLayer('cartodbpositron',name="light mode",control=True).add_to(m)
    
    # add full screen button
    folium.plugins.Fullscreen().add_to(m)
    
    # We add a layer controller
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Modify Marker template to include the onClick event
    click_template_marker = """{% macro script(this, kwargs) %}
        var {{ this.get_name() }} = L.marker(
            {{ this.location|tojson }},
            {{ this.options|tojson }}
        ).addTo({{ this._parent.get_name() }}).on('click', onClick);
    {% endmacro %}"""
    
    click_template_polyline = """{% macro script(this, kwargs) %}
        var {{ this.get_name() }} = L.layer(
            {{ this.location|tojson }},
            {{ this.options|tojson }}
        ).addTo({{ this._parent.get_name() }}).on('click', onClick);
    {% endmacro %}"""
    
    # Change template to custom template
    Marker._template = Template(click_template_marker)
    # Layer._template = Template(click_template_polyline)

    html = m.get_root()
    html.script.add_child(get_script_ant(m))
    
    # Add leaflet antpath plugin cdn link
    link = folium.JavascriptLink("https://cdn.jsdelivr.net/npm/leaflet-ant-path@1.3.0/dist/leaflet-ant-path.js")
    m.get_root().html.add_child(link)
    
    
    print(f'Data\mymap_{name}.html')
    m.save(f'Data\mymap_{name}.html')

def get_script_ant(m):
    # Create the onClick listener function as a branca element and add to the map html
    map_id = m.get_name()
    click_js = f"""function onClick(e) {{                
                        
                     var coords = e.target.options.pathCoords;
                     //var coords = JSON.stringify(coords);
                     //alert(coords);
                     var ant_path = L.polyline.antPath(coords, {{
                    "delay": 400,
                    "dashArray": [
                        10,
                        20
                    ],
                    "weight": 5,
                    "color": "#0000FF",
                    "pulseColor": "#FFFFFF",
                    "paused": false,
                    "reverse": false,
                    "hardwareAccelerated": true
                    }});                 
                    
                    ant_path.addTo({map_id});
                     }}"""
    # find a way to delete old ant paths ....
                     
    e = folium.Element(click_js)
    return e

def get_legend():
    # We import the required library:
    from branca.element import Template, MacroElement
    
    template = """
    {% macro html(this, kwargs) %}
    
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Strava Maps</title>
      <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    
      <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
      
      <script>
      $( function() {
        $( "#maplegend" ).draggable({
                        start: function (event, ui) {
                            $(this).css({
                                right: "auto",
                                top: "auto",
                                bottom: "auto"
                            });
                        }
                    });
    });
    
      </script>
    </head>
    <body>
    
     
    <div id='maplegend' class='maplegend' 
        style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
         border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
         
    <div class='legend-title'>Legend</div>
    <div class='legend-scale'>
      <ul class='legend-labels'>
        <li><span style='background:orange;opacity:0.7;'></span>Hike</li>
        <li><span style='background:red;opacity:0.7;'></span>Run</li>
        <li><span style='background:green;opacity:0.7;'></span>Bike</li>
        <li><span style='background:blue;opacity:0.7;'></span>Ski</li>      
    
      </ul>
    </div>
    </div>
     
    </body>
    </html>
    
    <style type='text/css'>
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    {% endmacro %}"""
    
    macro = MacroElement()
    macro._template = Template(template)
    
    return macro
    