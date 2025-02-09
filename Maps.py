# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:47:12 2025

@author: celine
"""

import folium
import numpy as np
import Settings as st
import ProcessData as pr
import ScriptsMaps as scm
from folium.plugins import OverlappingMarkerSpiderfier
from folium.map import Marker, Template
from folium.vector_layers import PolyLine
from branca.element import MacroElement



#TODO: import gpx/polyline/similar by user to the map
#TODO: link with other data sources (ut, etc.)
#TODO: generate graphs a la volée instead of at the start


class MapStrava():
    def __init__(self, dfmax, name):
        location = pr.centroid(dfmax['latlng'])
        self.map = folium.Map(location=location, zoom_start=4)
        self.profiles = {}
        self.groups_activity = {}
        for type_activity in dfmax.type.unique():
            if type_activity in st.typact_map:
                self.groups_activity[type_activity] = folium.FeatureGroup(name=type_activity).add_to(self.map)
        
        self.marker_cluster = folium.plugins.MarkerCluster(name="Markers").add_to(self.map)
        self.plot_activities(dfmax)
        self.add_other_elements(location)
        self.add_scripts()
        self.add_control_layers()

        print(f'Data\mymap_{name}.html')
        self.map.save(f'Data\mymap_{name}.html')
    
    def add_scripts(self):
        # Change template to custom template
        Marker._template = Template(scm.macro_marker())
        PolyLine._template = Template(scm.macro_polyline())

        html = self.map.get_root()
        map_id = self.map.get_name()
        # html.script.add_child(folium.Element(scm.add_file2(map_id)))
        # html.script.add_child(folium.Element(scm.add_file()))
        html.script.add_child(folium.Element(scm.click_on(map_id)))
        html.script.add_child(folium.Element(scm.hover_in(map_id)))
        html.script.add_child(folium.Element(scm.hover_out(map_id)))
        
        # Add leaflet antpath plugin cdn link
        link = folium.JavascriptLink("https://cdn.jsdelivr.net/npm/leaflet-ant-path@1.3.0/dist/leaflet-ant-path.js")
        self.map.get_root().html.add_child(link)
        
    
    def add_control_layers(self):
        
        # Add dark and light mode. 
        folium.TileLayer('cartodbdark_matter',name="dark mode",control=True,show=False).add_to(self.map)
        folium.TileLayer('cartodbpositron',name="light mode",control=True,show=False).add_to(self.map)

        # Add Avalanche info Norway
        data_NOR = [{"url":r"https://nve.geodataonline.no:443/arcgis/services/Bratthet/MapServer/WmsServer?",
                     "layers":'Bratthet_snoskred',
                     "name":'Slopes NOR',
                     "opacity":0.6,
                     "min_zoom":5},
                    {"url":r"https://nve.geodataonline.no:443/arcgis/services/SkredHendelser1/MapServer/WmsServer?",
                     "layers":'Skredtype',
                     "name":'Historic avalanche NOR',
                     "opacity":0.6,
                     "min_zoom":10}]
        for layer in data_NOR:
            folium.WmsTileLayer(fmt="image/png",
                                attr="GeoNorge", transparent=True, overlay=True,
                                control=True, show=False,
                                **layer
                                ).add_to(self.map)
            
        # Add Avalanche info France
        url_FRA = "https://data.geopf.fr/wms-r/wms?"
        data_FRA = [{"layers":'GEOGRAPHICALGRIDSYSTEMS.SLOPES.MOUNTAIN',
                     "name":'Slopes FRA',
                     "opacity":0.6,
                     "min_zoom":8},
                    {"layers":'ELEVATION.CONTOUR.LINE',
                     "name":'elevation lines FRA',
                     "opacity":0.8,
                     "min_zoom":8}]
        for layer in data_FRA:
            folium.WmsTileLayer(
                url=url_FRA, version="1.3.0", fmt="image/png",
                attr="IGN", transparent=True, overlay=True,
                control=True, show=False,
                **layer
                ).add_to(self.map)
        
        folium.WmsTileLayer(
            url="https://data.geopf.fr/wms-v/ows?SERVICE=WMS&",
            version="1.3.0", name='itinerary FRA', fmt="image/png",
            layers='TRACES.RANDO.HIVERNALE', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)
        
  
        # Add layers strava heatmap
        color_heatmap = {"all":"hot", "run":"hot", "ride":"hot", "winter":"purple"}
        for name in ["all", "run", "ride", "winter"]:
            folium.TileLayer(
                f'https://proxy.nakarte.me/https/heatmap-external-a.strava.com/tiles-auth/{name}/{color_heatmap[name]}/'+'{z}/{x}/{y}.png', 
                attr='to be written', 
                name=f'Strava heatmaps {name}',
                transparent=True, overlay=True, control=True, show=False,
                opacity=0.8,
                ).add_to(self.map)



        urlx = "https://wms.geonorge.no/skwms1/wms.friluftsruter2?"

        folium.WmsTileLayer(
            url=urlx,
            version="1.3.0", name='itinerary1 NOR', fmt="image/png",
            layers='Ruter', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)
        folium.WmsTileLayer(
            url=urlx,
            version="1.3.0", name='itinerary2 NOR', fmt="image/png",
            layers='Fotrutetype', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)
        folium.WmsTileLayer(
            url=urlx,
            version="1.3.0", name='itinerary3 NOR', fmt="image/png",
            layers='Skiløypepreparering', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)
        folium.WmsTileLayer(
            url=urlx,
            version="1.3.0", name='itinerary4 NOR', fmt="image/png",
            layers='Gradering', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)

        # Add shadows for moutains
        shadow_FRA = folium.WmsTileLayer(
            url=url_FRA,
            version="1.3.0", name='shadow FRA', fmt="image/png",
            layers='ELEVATION.ELEVATIONGRIDCOVERAGE.SHADOW', 
            attr="IGN", opacity=0.9, min_zoom=5,
            transparent=True,overlay=True,control=False,show=True,
            )
        
        shadow_NOR = folium.WmsTileLayer(
            url="https://wms.geonorge.no/skwms1/wms.fjellskygge?language=Norwegian&",
            version="1.3.0", name='shadow NOR', fmt="image/png",
            layers='fjellskygge', 
            attr="GeoNorge", opacity=0.8, min_zoom=5,
            transparent=True,overlay=True,control=False,show=True,
            )
        
        folium.WmsTileLayer(
            url="https://basemap.nationalmap.gov:443/arcgis/services/USGSShadedReliefOnly/MapServer/WMSServer?",
            version="1.3.0", name='shadow USA', fmt="image/png",
            layers='0', 
            attr="GeoNorge", opacity=0.35, min_zoom=5,
            transparent=True,overlay=True,control=True,show=False,
            ).add_to(self.map)
        

        
        
        # "https://services.arcgisonline.com/arcgis/rest/services/Elevation/World_Hillshade/MapServer/WMTS/tile/1.0.0/"
        # "https://services.arcgisonline.com/arcgis/rest/services/Elevation/World_Hillshade/MapServer/WMTS?"
        # Elevation_World_Hillshade
        
        
        shadow_FRA.add_to(self.map)
        shadow_NOR.add_to(self.map)

        self.map.keep_in_front(shadow_NOR, shadow_FRA)
        
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
        macro = MacroElement()
        macro._template = Template(scm.get_legend_map())
        self.map.get_root().add_child(macro)
        
        # add full screen button
        folium.plugins.Fullscreen().add_to(self.map)
        
        # add search bar
        folium.plugins.Geocoder().add_to(self.map)        
        
    
    def plot_activities(self, dfmax):
        for idx, row in dfmax.iterrows():
            if row['latlng'] not in ["", 0, "0", np.nan] and row["type"] in st.typact_map: # Activities with no spatial data are ignored
                self.plot_activity(row)
    
    def plot_activity(self, act):
        activity_type = act['type']
        # Activity info popup
        resolution, width, height = 75, 6, 5
        iframe = folium.IFrame(scm.get_popup_html(act),
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

    

def get_map(dfmax, name):
    """ Write a html file containing a map of all activities.
    
    Parameters
    ----------
    dfmax : Dataframe with both activities and stream data
    name : name to be used for the output file

    Returns: None.

    """
    MapStrava(dfmax, name)
    