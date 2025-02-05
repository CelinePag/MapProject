# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:47:12 2025

@author: celine
"""

import folium
import numpy as np
import Settings as st
import ProcessData as pr
from folium.plugins import OverlappingMarkerSpiderfier
from folium.map import Marker, Template, Layer


#TODO: import gpx/polyline/similar by user to the map
#TODO: link with other data sources (ut, etc.)
#TODO: generate graphs a la volée instead of at the start


def centroid(polylines):
    """ return the mean coordinates of all activities with spatial data """
    x, y = [], []
    for idx, polyline in polylines.items():
        if polyline not in ["", 0, "0", np.nan]:
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
            if type_activity in st.typact_sport:
                self.groups_activity[type_activity] = folium.FeatureGroup(name=type_activity).add_to(self.map)
        
        self.marker_cluster = folium.plugins.MarkerCluster(name="Markers").add_to(self.map)
        self.plot_activities(dfmax)
        self.add_other_elements(location)
        self.add_scripts()
        self.add_control_layers()

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
        
        click_template_polyline = """{% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.polyline(
                {{ this.location|tojson }},
                {{ this.options|tojson }}
            ).addTo({{ this._parent.get_name() }}).on('click', onClick);
        {% endmacro %}"""
        

        # Change template to custom template
        Marker._template = Template(click_template_marker)
        
        Layer._template = Template(click_template_polyline)

        html = self.map.get_root()
        html.script.add_child(get_script_ant(self.map.get_name()))
        
        # Add leaflet antpath plugin cdn link
        link = folium.JavascriptLink("https://cdn.jsdelivr.net/npm/leaflet-ant-path@1.3.0/dist/leaflet-ant-path.js")
        self.map.get_root().html.add_child(link)
        
    
    def add_control_layers(self):
        
        # Add dark and light mode. 
        folium.TileLayer('cartodbdark_matter',name="dark mode",control=True,show=False).add_to(self.map)
        folium.TileLayer('cartodbpositron',name="light mode",control=True,show=False).add_to(self.map)
        # folium.TileLayer('Thunderforest.OpenCycleMap',name="Cyclo map",control=True,show=False).add_to(self.map)
        # folium.TileLayer('Thunderforest.Outdoors',name="Outdoor map",control=True,show=False).add_to(self.map)
        # folium.TileLayer('Thunderforest.SpinalMap',name="Try me",control=True,show=False).add_to(self.map)

        
            
        # Add Avalanche info Norway
        data = [("Bratthet_snoskred", 'Slopes NOR', r"https://nve.geodataonline.no:443/arcgis/services/Bratthet/MapServer/WmsServer?", 1),
                ("Skredtype", 'Historic avalanche NOR', r"https://nve.geodataonline.no:443/arcgis/services/SkredHendelser1/MapServer/WmsServer?", 11)]
        # avalanche_NO_data = {l:folium.FeatureGroup(name=f'{n}').add_to(self.map) for (l,n,_,_) in data}
        for (l,n,s,z) in data:
            folium.WmsTileLayer(
                url=s,
                name=f'{n}', 
                fmt="image/png",
                layers=f'{l}', 
                transparent=True,
                opacity=0.6,
                overlay=True,
                control=True,
                show=False,
                min_zoom=z,
            ).add_to(self.map)
            # self.map.add_child(avalanche_NO_data[l])
            
        # Add Avalanche info France
        folium.WmsTileLayer(
            url="https://data.geopf.fr/wms-r/wms?",
            version="1.3.0" ,
            name='Slopes FRA', 
            fmt="image/png",
            layers='GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN', 
            attr="IGN",
            opacity=0.6,
            transparent=True,
            overlay=True,
            control=True,
            show=False,
            min_zoom=8,
        ).add_to(self.map)
        
        # Add layers strava heatmap
        color_heatmap = {"all":"hot", "run":"hot", "ride":"hot", "winter":"purple"}
        # strava_data = {f"{name}":folium.FeatureGroup(name=f'strava_{name}').add_to(self.map) for name in ["all", "run", "ride", "winter"]}
        for name in ["all", "run", "ride", "winter"]:
            folium.TileLayer(f'https://proxy.nakarte.me/https/heatmap-external-a.strava.com/tiles-auth/{name}/{color_heatmap[name]}/'+'{z}/{x}/{y}.png', 
                     attr='to be written', 
                     name=f'Strava heatmaps {name}',
                     transparent=True,
                     overlay=True,
                     control=True,
                     show=False,
                     opacity=0.8,
                     ).add_to(self.map)
            # self.map.add_child(strava_data[name])

        
        # We add a layer controller
        folium.LayerControl(collapsed=False).add_to(self.map)
        # Add separated layer control for activities
        folium.plugins.GroupedLayerControl(groups={'My activities': self.groups_activity.values()},
                                            exclusive_groups=False,
                                            collapsed=False,).add_to(self.map)
        # # Add separated layer control for avalacnche norway
        # folium.plugins.GroupedLayerControl(groups={'Avalanche Norway': list(avalanche_NO_data.values())},
        #                                     exclusive_groups=False,
        #                                     collapsed=True,).add_to(self.map)
        # # separated cl for stravas heatmaps
        # folium.plugins.GroupedLayerControl(groups={'Strava Data': list(strava_data.values())},
        #                                    exclusive_groups=False,
        #                                    collapsed=True,).add_to(self.map)
    
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
        
        # add full screen button
        folium.plugins.Fullscreen().add_to(self.map)
        
        # add search bar
        folium.plugins.Geocoder().add_to(self.map)        
        
    
    def plot_activities(self, dfmax):
        for idx, row in dfmax.iterrows():
            if row['latlng'] not in ["", 0, "0", np.nan] and row["type"] in st.typact_sport: # Activities with no spatial data are ignored
                self.plot_activity(row)
    
    def plot_activity(self, act):
        activity_type = act['type']
        # Activity info popup
        resolution, width, height = 75, 6, 5
        iframe = folium.IFrame(self.get_popup_html(act),
                               width=(width*resolution)+20,
                               height=(height*resolution)+20)
        popup = folium.Popup(iframe, max_width=2650)
        
        poly = folium.PolyLine(st.listliststr_to_listlist(act['latlng']),
                                                            color=st.color_activities[act['type']],
                                                            Highlight= True,
                                                            show=True,
                                                            overlay=True,
                                                            tooltip=act['name'],
                                                            # popup=popup,
                                                            pathCoords=st.listliststr_to_listlist(act['latlng']))
        
        # poly.add_child(popup)
        self.groups_activity[activity_type].add_child(poly)
        
        # add marker to map
        halfway_coord = st.listliststr_to_listlist(act['latlng'])[int(len(st.listliststr_to_listlist(act['latlng']))/2)]
        icon = folium.Icon(color='black',
                           icon_color=st.color_activities[act['type']],
                           icon='info-sign')
        marker = folium.Marker(location=halfway_coord,
                               popup=popup,
                               lazy=True,
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
            # self.profiles["Speed"][act['id']], 
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
                    "delay": 800,
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
                     
                    {map_id}.eachLayer(function(layer){{
                    if (layer instanceof L.Polyline.AntPath)
                       {{ {map_id}.removeLayer(layer) }}
                       }});

                    ant_path.addTo({map_id});
                     }}"""
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
         border-radius:6px; padding: 10px; font-size:14px; left: 20px; bottom: 20px;'>
         
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
    