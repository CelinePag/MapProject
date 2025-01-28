# -*- coding: utf-8 -*-
"""
Created on Sun Jan  5 15:43:38 2025

@author: celine
"""

import requests
import json
import time
from stravalib.client import Client
import pandas as pd

PATH_TOKEN = r"Data\tokens"
PATH_CSV = r"Data"

class ClientStrava:
    def __init__(self, name): #id_athlete, id_secret, name_file):
        with open(f"{PATH_TOKEN}\{name}.json") as json_file:
            user_data = json.load(json_file)
        self.id_athlete = user_data["id"]
        self.id_secret = user_data["secret_key"]
        self.name_file = f"{user_data['tokenFile']}"
        self.nom = user_data["name"]
        if self.name_file in [None, 0, "0"]:
            self.create_client(name)
            user_data['tokenFile'] = f"strava_tokens_{name}.json"
            with open(f"{PATH_TOKEN}\{name}.json", "w") as outfile:
                 json.dump(user_data, outfile)
        self.name_file = f"{PATH_TOKEN}\{user_data['tokenFile']}"
        self.init_client()

    
    def create_client(self, name):
        print(f"http://www.strava.com/oauth/authorize?client_id={self.id_athlete}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all,profile:read_all")
        code = input("code:")
        response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': self.id_athlete,
                                'client_secret': self.id_secret,
                                'code': code, #"0cb76cf181e2d3e55dbac35cc439a99e7727de1e",
                                'grant_type': 'authorization_code'
                                })
        #Save json response as a variable
        strava_tokens = response.json()# Save tokens to file
        with open(f"{PATH_TOKEN}\strava_tokens_{name}.json", 'w') as outfile:
            json.dump(strava_tokens, outfile)

    def init_client(self):
        with open(self.name_file) as json_file:
            strava_tokens = json.load(json_file)
            ## If access_token has expired then use the refresh_token to get the new access_token
        if strava_tokens['expires_at'] < time.time():
            #Make Strava auth API call with current refresh token
            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': self.id_athlete,
                                        'client_secret': self.id_secret,
                                        'grant_type': 'refresh_token',
                                        'refresh_token': strava_tokens['refresh_token']
                                        }
                            )#Save response as json in new variable
            new_strava_tokens = response.json()# Save new tokens to file
            with open(self.name_file, 'w') as outfile:
                json.dump(new_strava_tokens, outfile)#Use new Strava tokens from now
            strava_tokens = new_strava_tokens#Loop through all activities
            
        self.client = Client()
        self.client.access_token = strava_tokens['access_token']
        self.client.refresh_token = strava_tokens['refresh_token']
        self.client.token_expires_at = strava_tokens['expires_at']



class Activities:
    def __init__(self, client, nom):
        self.client = client
        self.init_csv(nom)
        self.df = pd.read_csv(f'{PATH_CSV}\strava_activities_{nom}.csv')
        
    def init_csv(self, nom):      
        athlete = self.client.get_athlete()
        print("Athlete's name is {} {}, based in {}, {}"
              .format(athlete.firstname,
                      athlete.lastname,
                      athlete.city,
                      athlete.country))
        
        my_cols = [
                "name",
                "start_date_local",
                "type",
                "sport_type",
                "distance",
                "moving_time",
                "elapsed_time",
                "total_elevation_gain",
                "average_heartrate",
                "max_heartrate",
                "average_speed",
                "max_speed",
                "elev_high",
                "elev_low",
                "private",
                "visibility",
                "has_heartrate",
                "suffer_score"]
        
        activities = self.client.get_activities(limit=1000)
        data = []
        for activity in activities:
            my_dict = activity.to_dict()
            data.append([activity.id]+[my_dict.get(x) for x in my_cols])
            
        # Add id to the beginning of the columns, used when selecting a specific activity
        my_cols.insert(0,'id')
        df = pd.DataFrame(data, columns=my_cols)
        # Make all walks into hikes for consistency
        df['type'] = df['type'].replace('Walk','Hike')
        df['distance_km'] = df['distance']/1e3
        df['average_pace'] = (1/0.06)/df['average_speed']
        df['average_speed_kmh'] = df['average_speed']*3.6
        df['max_speed_kmh'] = df['max_speed']*3.6
        df['start_date_local'] = pd.to_datetime(df['start_date_local'])
        df['hour_of_day'] = df['start_date_local'].dt.time
        df['day_of_week'] = df['start_date_local'].dt.day_name()
        df['month_of_year'] = df['start_date_local'].dt.month
        df['moving_time_bis'] = 1*df['moving_time']
        df['moving_time'] = pd.to_timedelta(df['moving_time'])
        df['elapsed_time'] = pd.to_timedelta(df['elapsed_time'])
        df['elapsed_time_hr'] = df['elapsed_time'].astype('int64')/3600e9
        df['moving_time_hr'] = df['moving_time'].astype('int64')/3600e9
        df.to_csv(f'{PATH_CSV}\strava_activities_{nom}.csv')


    def init_csv_streams(self, df, nb=50, name=""):
        nom2 = self.client.get_athlete().firstname
        try:
            old = pd.read_csv(f'{PATH_CSV}\strava_activities_stream_{nom2}_{name}.csv').fillna(0)
        except:
            print("old file not found")
            old = None
        
        types = ['time', 'distance', "heartrate", 'latlng', 'altitude',
                 'velocity_smooth', 'moving', 'grade_smooth', "cadence"]
        data = []
        nb_request = 0
        for idx,row in df.iterrows():
            if (old is None) or (old is not None and df['id'][idx] not in old["id"].values):
                if nb_request > nb:
                    break
                activity_data=self.client.get_activity_streams(df['id'][idx], types=types)
                subdata=[df['id'][idx]]
                for el in types:
                    try:
                        subdata.append(activity_data[el].data)
                    except KeyError:
                        subdata.append(None)
                data.append(subdata)
                nb_request += 1
        print("nb request:", nb_request)
        types.insert(0,'id')
        df2 = pd.DataFrame(data, columns=types)
        pd.concat([old, df2]).to_csv(f'{PATH_CSV}\strava_activities_stream_{nom2}_{name}.csv')
