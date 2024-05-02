from pymongo import MongoClient
import requests
import os
import datetime as dt
import json
import time

manual_review_dict={}
final_violation_dict={}
#Manually update the blacklist manually if required
blacklist=['1e9xSzofGkkCaFkuAuYyr8', '5grlVJ5ImEn2c45DQCTCLE', '4VN7J0uq62foOhZndwOegy', 
'6Dt8seXTiv3ppvEEQqOoNi', '70LyO3sxFcgGcxBEA9F8Oz', '1t9coKpQTkNU1emgPoh9Bm', '56QZCW8bgrYOHWAuU8CLvu', 
'5yCH14G9XKGNSjI0QZaA2I', '0n5tTNtf1IEgYVr8JjTkir', '0QJ9OwBCxkuF6qxXR02pAG', '4eNmgC3cSvJ7loX3TmB4Ln', 
'1oXqgF4EZMWNeAqODjZfZP', '2Hqr11IChE5XDIlGneSuYK', '46XK8JHNNU1yw41vajemjZ', '0Zn3zPGUWpfFucSuVWT8ME', 
'0632xmueZBTGdtzdypdYz8', '0HZHyPI4rzahBJfKPMu9V8', '7ID344mcNuUgvPRUR1azsY', '2JsvsBxDj5ugTWPqrB29xk', 
'0asnMF4Hejnkv1CZWbzkPg', '5wyeMOhpEUIeDoEIXHWZwp', '4SNitBfBk25IB0gc2TtCh4', '1bUtoIcwIp7E53iLbw9TRD', 
'0XmDDj7YP5AIEm8zOosHor', '3SCY3GfBRDWcU1ldjAO7Es', '5laQJrkgGf0RD4Gcu8FRqo', '44ptnXNlPRWCYqiUwA1bHk', 
'19t15R3YRj2yC1VRPew69Z', '3yHTttoNImQoKI9o1j2fQL', '3VqGQlKyK2KoRRn4gITKnY', '46kNBi7S0v9f5INZ3F1d6L']


class SpotifyConnection:
    def __init__(self):
        self.grant_type='client_credentials'
        self.auth_url='https://accounts.spotify.com/api/token'
        
    def connect(self):
        auth_response = requests.post(self.auth_url, {
            'grant_type': self.grant_type,
            'client_id': os.environ['client_id'],
            'client_secret': os.environ['client_secret'],
        })
            # convert the response to JSON
        auth_response_data = auth_response.json()
        # save the access token
        access_token = auth_response_data['access_token']
        my_headers = {
            'Authorization': 'Bearer {token}'.format(token=access_token)
        }
        return my_headers
        
class MongoConnection:
    def __init__(self):
        self.mong_auth_string=os.environ['MONGO_URI']

        
    def connect(self, database_name):
        client = MongoClient(self.mong_auth_string, serverSelectionTimeoutMS=60000)
        playlist_curator_data=client.get_database(database_name)
        return playlist_curator_data



def addToViolationDict(playlist_id, rule_violated, values):
    final_violation_dict[playlist_id]={
        'rule_violated': rule_violated,
        'values': values
    }
        
def daysSinceLastUpdate(playlist_id):
    days_since_last_update=follower_counts_collection.find_one({'playlist_id': playlist_id})['days_since_last_update']
    print("Checking days since last update as ", days_since_last_update)
    return days_since_last_update

def calculateNumberOfTracks(playlist_id):
    number_of_tracks=len((audio_features_collection.find_one({'playlist_id': playlist_id}))['track_ids'])
    print("Checking number of tracks as  ", number_of_tracks)
    return number_of_tracks


def calculateNumberOfFollowers(playlist_id):
    number_of_followers=list(follower_counts_collection.find_one({'playlist_id': playlist_id})['playlist_follower_count'].values())[-1]
    print("Checking number of followers as   ", number_of_followers)
    return number_of_followers

def calculateSmoothness(playlist_id):
    smoothness_score=follower_counts_collection.find_one({'playlist_id': playlist_id})['smoothness_score']
    print("Checking smoothness score as   ", smoothness_score)
    return smoothness_score

def setStatus(playlist_id, current_status, new_status):
    query = {"playlist_id": playlist_id}
    new_status_update = {"$set": {"status": new_status}}
    audio_features_collection.update_one(query, new_status_update)
    print(str(f"{playlist_id} has been updated from {current_status} to {new_status}"))
    return str(f"{playlist_id} has been updated from {current_status} to {new_status}")
    

#Program starts
MongoConnectionInstance=MongoConnection()
audio_analysis_db=MongoConnectionInstance.connect('AUDIO_ANALYSIS')
audio_features_collection=audio_analysis_db.PLAYLIST_AUDIO_FEATURE

curator_data_db=MongoConnectionInstance.connect('PLAYLIST_CURATOR_DATA')
follower_counts_collection=curator_data_db.FOLLOWER_COUNTS


SpotifyConnectionInstance=SpotifyConnection()
spotify_headers=SpotifyConnectionInstance.connect()

# count=0

for item in audio_features_collection.find():
    print("---------")
    playlist_id=item['playlist_id']
    print(playlist_id)
    status=item['status']
    flag=True

    #Check if playlist exists on Spotify
    playlistURL='https://api.spotify.com/v1/playlists/'+playlist_id
    playlist_response_code=str(requests.get(playlistURL, headers=spotify_headers))
    if playlist_response_code== "<Response [404]>":
            print("Checking if playlist exists on Spotify")
            myquery = { "playlist_id": playlist_id }
            try:
                audio_features_collection.delete_one(myquery)
            except:
                print('Unable to find playlist in audio_features_collection')
            
            try:
                follower_counts_collection.delete_one(myquery)
            except:
                print('Unable to find playlist in follower_counts_collection')
            continue
    

    #Need to create a simple list of playlist IDs which are flagged by manual review as botted called as Blacklist
    if playlist_id in blacklist:    
        print("Playlist is blacklisted")
        flag=False 
        addToViolationDict(playlist_id, 'blacklisted', '')
        

    #get days_since_last_upload
    days_since_last_update=daysSinceLastUpdate(playlist_id)
    if days_since_last_update>90:
        flag=False
        addToViolationDict(playlist_id, 'daysSinceLastUpload', values={'days_since_last_upload': days_since_last_update}), 
        

    #get number_of_tracks
    number_of_tracks=calculateNumberOfTracks(playlist_id)
    if number_of_tracks<10 or number_of_tracks>360 :
        flag=False
        addToViolationDict(playlist_id, 'numberOfTracks', values={'number_of_tracks': number_of_tracks})
        

    #get number_of_followers
    number_of_followers=calculateNumberOfFollowers(playlist_id)
    if number_of_followers<70:
        flag=False
        addToViolationDict(playlist_id, 'NumberOfFollowers', values={'number_of_followers': number_of_followers})
        
    #     #get smoothness_score
    smoothness_score=calculateSmoothness(playlist_id)
    if smoothness_score<0.0009:
        flag=False
        addToViolationDict(playlist_id, 'smoothnessScore', values={'smoothness_score': smoothness_score})
        


    #If code reaches here, it means all checks were passed and so invalid playlists can change to U. 
    if flag==False:
        setStatus(playlist_id, status, 'I')
    elif status=='I':
        setStatus(playlist_id, status, 'U')
    else:
        continue

    count=count+1
    if count==10:
        break

    # count=count+1
    # if count==10:
    #     break

print("Final violation dictionary   --- " , final_violation_dict)
