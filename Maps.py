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


def centroid(polylines):
    """ return the mean coordinates of all activities with spatial data """
    x, y = [], []
    for idx, polyline in polylines.items():
        if polyline not in ["", 0, "0"]:
            for coord in st.listliststr_to_listlist(polyline):
                x.append(coord[0])
                y.append(coord[1])
    return [(min(x)+max(x))/2, (min(y)+max(y))/2]


class MapStrava():
    def __init__(self, dfmax, name):
        location = centroid(dfmax['latlng'])
        self.map = folium.Map(location=location, zoom_start=4)
        self.profiles = {}
        for profile_name, col_name in zip(["Elevation", "Speed"],
                                          ["altitude", "velocity_smooth"]):
            self.profiles[profile_name] = pr.get_profiles(dfmax,
                                                          x_axe={"name":"Distance", "col_name":"distance_y"},
                                                          y_axe={"name":profile_name, "col_name":col_name})
        self.groups_activity = {}
        for type_activity in dfmax.type.unique():
            self.groups_activity[type_activity] = folium.FeatureGroup(name=type_activity).add_to(self.map)
        
        self.marker_cluster = folium.plugins.MarkerCluster(name="markers").add_to(self.map)
        self.plot_activities(dfmax)
        self.add_other_elements(location)
        self.add_scripts()

        print(f'Data\mymap_{name}.html')
        self.map.save(f'Data\mymap_{name}.html')
    
    def add_scripts(self):
        # Modify Marker template to include the onClick event
        click_template_marker = """{% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.marker(
                {{ this.location|tojson }},
                {{ this.options|tojson }}
            ).addTo({{ this._parent.get_name() }}).on('click', onClick);
        {% endmacro %}"""
        

        # Change template to custom template
        Marker._template = Template(click_template_marker)

    
        html = self.map.get_root()
        html.script.add_child(get_script_ant(self.map.get_name()))
        
        # Add leaflet antpath plugin cdn link
        link = folium.JavascriptLink("https://cdn.jsdelivr.net/npm/leaflet-ant-path@1.3.0/dist/leaflet-ant-path.js")
        self.map.get_root().html.add_child(link)
        
    
    def add_other_elements(self, location):
        # Add the OverlappingMarkerSpiderfier plugin
        oms = OverlappingMarkerSpiderfier(
            keep_spiderfied=True,  # Markers remain spiderfied after clicking
            nearby_distance=20,  # Distance for clustering markers in pixel
            circle_spiral_switchover=10,  # Threshold for switching between circle and spiral
            leg_weight=2.0  # Line thickness for spider legs
            )
        oms.add_to(self.map)
        
        # Add legend
        self.map.get_root().add_child(get_legend())
        
        # Add dark and light mode. 
        folium.TileLayer('cartodbdark_matter',name="dark mode",control=True).add_to(self.map)
        folium.TileLayer('cartodbpositron',name="light mode",control=True).add_to(self.map)
        
        # add full screen button
        folium.plugins.Fullscreen().add_to(self.map)
        
        # add search bar
        folium.plugins.Geocoder().add_to(self.map)
        
        #cluster markers
        # icon_create_function = """\
        # function(cluster) {
        #     return L.divIcon({
        #     html: '<b>' + cluster.getChildCount() + '</b>',
        #     className: 'marker-cluster marker-cluster-large',
        #     iconSize: new L.Point(20, 20)
        #     });
        # }"""
        # marker_cluster = folium.plugins.MarkerCluster(locations=location,
        #                                               name="1000 clustered icons",
        #                                               overlay=True,
        #                                               control=True,
        #                                               icon_create_function=icon_create_function,)

        # marker_cluster.add_to(self.map)
        
        # We add a layer controller
        folium.LayerControl(collapsed=False).add_to(self.map)
    
    def plot_activities(self, dfmax):
        for idx, row in dfmax.iterrows():
            if row['latlng'] not in ["", 0, "0"]: # Activities with no spatial data are ignored
                self.plot_activity(row)
    
    def plot_activity(self, act):
        activity_type = act['type']
        self.groups_activity[activity_type].add_child(folium.PolyLine(st.listliststr_to_listlist(act['latlng']),
                                                                    color=st.color_activities[act['type']],
                                                                    Highlight= True,
                                                                    show=True,
                                                                    overlay=True,
                                                                    tooltip=act['name'],
                                                                    pathCoords=st.listliststr_to_listlist(act['latlng'])))
        halfway_coord = st.listliststr_to_listlist(act['latlng'])[int(len(st.listliststr_to_listlist(act['latlng']))/2)]
        
        
        # add marker to map
        resolution, width, height = 75, 6, 6.5
        iframe = folium.IFrame(self.get_popup_html(act),
                               width=(width*resolution)+20,
                               height=(height*resolution)+20)

        popup = folium.Popup(iframe, max_width=2650)
        icon = folium.Icon(color='black',
                           icon_color=st.color_activities[act['type']],
                           icon='info-sign')
        marker = folium.Marker(location=halfway_coord,
                               popup=popup,
                               icon=icon,
                               tooltip=act['name'],
                               pathCoords=st.listliststr_to_listlist(act['latlng']))
        
        # self.groups_activity[activity_type].add_child(marker)
        marker.add_to(self.marker_cluster)

        
    def get_popup_html(self, act):
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
            act['name'], 
            act["start_date_local"].split(" ")[0], 
            act["hour_of_day"],  
            act['type'], 
            act['distance_km'], 
            act['total_elevation_gain'], 
            int(act['moving_time_hr']),
            (act['moving_time_hr']% 1)*60, 
            act['average_speed_kmh'],
            act['max_speed_kmh'], 
            float(act['average_heartrate']),
            float(act['max_heartrate']),
            self.profiles["Elevation"][act['id']],
            self.profiles["Speed"][act['id']], 
        )
        return html

def get_map(dfmax, name):
    """ Write a html file containing a map of all activities.
    
    Parameters
    ----------
    dfmax : Dataframe with both activities and stream data
    name : name to be used for the output file

    Returns: None.

    """
    MapStrava(dfmax, name)


def get_script_ant(map_id):
    # Create the onClick listener function as a branca element and add to the map html
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
    # {map_id}.eachLayer(function(layer){{
    # if (layer instanceof L.Polyline.antpath)
    #    {{ {map_id}.removeLayer(layer) }}
    #    }});
                     
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
    