# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 23:29:20 2025

@author: celine
"""

import ProcessData as pr


def get_popup_html(act):
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
        act['sport_type'], 
        act['distance_km'], 
        act['total_elevation_gain'], 
        int(act['moving_time_hr']),
        (act['moving_time_hr']% 1)*60, 
        act['average_speed_kmh'],
        act['max_speed_kmh'], 
        float(act['average_heartrate']),
        float(act['max_heartrate']),
        # self.profiles["Elevation"][act['id']],
        pr.get_profile_id(act,
                          x_axe={"name":"Distance", "col_name":"distance_y"},
                          y_axe={"name":"Elevation", "col_name":"altitude"})
        # self.profiles["Speed"][act['id']], 
    )
    return html


def macro_marker():
    template_marker = """{% macro script(this, kwargs) %}
                    var {{ this.get_name() }} = L.marker(
                        {{ this.location|tojson }},
                        {{ this.options|tojson }}
                    ).addTo({{ this._parent.get_name() }});
                    {{ this.get_name() }}.on('click', onClick);
                    {{ this.get_name() }}.on('mouseover', hover_in);
                    {{ this.get_name() }}.on('mouseout', hover_out);
                {% endmacro %}"""
    return template_marker

def macro_polyline():
    template_polyline = """
                        {% macro script(this, kwargs) %}
                            var {{ this.get_name() }} = L.polyline(
                                {{ this.locations|tojson }},
                                {{ this.options|tojson }}
                            ).addTo({{ this._parent.get_name() }});
                            {{ this.get_name() }}.on('click', onClick);
                            {{ this.get_name() }}.on('mouseover', hover_in);
                            {{ this.get_name() }}.on('mouseout', hover_out);
                        {% endmacro %}
                        """
    return template_polyline


def click_on(map_id):
    js = f"""function onClick(e) {{                
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
    return js


def hover_in(map_id):
    js = f"""function hover_in(e) {{                
             var coords = e.target.options.pathCoords;
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
            ant_path.addTo({map_id});
             }}"""
    return js

def hover_out(map_id):
    js = f"""function hover_out(e) {{                
                    {map_id}.eachLayer(function(layer){{
                    if (layer instanceof L.Polyline.AntPath)
                       {{ {map_id}.removeLayer(layer) }}
                       }});
                     }}"""
    return js

def get_legend_map():
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
    return template

