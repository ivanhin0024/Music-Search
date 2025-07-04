from io import BytesIO
from tkinter import Button, Image, Label
import tkinter as tk 
from tkinter import messagebox
import customtkinter as ctk
import json
from dotenv import load_dotenv 
import os 
import base64
from requests import post, get
import requests
from PIL import ImageTk, Image

load_dotenv()


# client id from https://developer.spotify.com/dashboard/3f3557fc81014616b607dae9f6eaa247 
client_id = os.getenv('CLIENT_ID')
client_sercet = os.getenv('CLIENT_SERCET')

# Gets access token from Spotufy API using a client ID and client secret 
def get_token():
    auth_string = client_id + ':' + client_sercet
    auth_bytes = auth_string.encode('utf_8')
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization':'Basic ' + auth_base64, 
        'Content-Type':'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result['access_token']
    return token 
 
 # Rutruns the authorization header needed for using API requests 
def get_auth_header(token):
    return {'Authorization': 'Bearer  ' + token}

# searches for the artists using spotify and returns matched query
def search_for_artist(token, artist_name): 
    url  = 'https://api.spotify.com/v1/search'
    headers = get_auth_header(token)
    query = f'?q={artist_name}&type=artist&limit=1'

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)['artists']['items']
    if len(json_result) == 0:
        print('No aritst with this name exists...')
        return None
    
    return json_result[0]

# gets albums from searched artist 
def get_albums_by_artist(token, artist_id):
    url = f'https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album&market=US'
    headers =get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)['items']
    return json_result

#gets songs from searched artists
def get_songs_by_artist(token, artist_id):
    url  = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US'
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)['tracks']
    return json_result

#function triggered after user hits search and gets the artists songs and albums
def search(entry, token):
    artist_name = entry.get()
    result = search_for_artist(token, artist_name)
    if result:
        artist_id = result['id']
        songs = get_songs_by_artist(token, artist_id)
        top_songs = '\n'.join([f'{idx + 1:2}. {song['name']}'for idx, song in enumerate(songs)])
        messagebox.showinfo('Top Songs', top_songs)

#GUI 
ctk.set_appearance_mode('System')

ctk.set_default_color_theme('green')

appWitch, appHeight = 1100, 950

class App(ctk.CTk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title('Music API')
        self.geometry(f'{appWitch}x{appHeight}')

        frame = ctk.CTkFrame(self)
        frame.pack(expand=True, fill='both')

        # Left side of the main frame
        left_frame = ctk.CTkFrame(frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=20, pady=20)

        # Top section for artist search and image
        top_section = ctk.CTkFrame(left_frame)
        top_section.pack(side='top', fill='x', padx=20, pady=20)

        self.searchLabel = ctk.CTkLabel(top_section, text='Enter in the artist name')
        self.searchLabel.pack(side='left', padx=20, pady=20)

        search_frame = ctk.CTkFrame(top_section)
        search_frame.pack(side='left', pady=20, padx=20) 

        self.searchEntry = ctk.CTkEntry(search_frame, placeholder_text='Search')
        self.searchEntry.pack(side=tk.LEFT)

        self.searchButton = Button(search_frame, text="Search", command=self.perform_search, background='cornsilk')
        self.searchButton.pack(side=tk.LEFT, padx=15)

        self.artistImageLabel = Label(top_section, background='dimgrey')
        self.artistImageLabel.pack(side='right', padx=20, pady=20)

        # Middle section for top songs
        middle_section = ctk.CTkFrame(left_frame)
        middle_section.pack(side='top', fill='both', expand=True, padx=20, pady=20)

        top_songs_label = ctk.CTkLabel(middle_section, text="Top Songs", font=('Arial', 16, 'bold'))
        top_songs_label.pack(side='top', padx=20, pady=20)

        self.resultLabel = ctk.CTkLabel(middle_section, text="", wraplength=400)
        self.resultLabel.pack(side='top', padx=20, pady=20)

        # Bottom section for top albums
        bottom_section = ctk.CTkFrame(left_frame)
        bottom_section.pack(side='bottom', fill='both', expand=True, padx=20, pady=20)

        albums_label = ctk.CTkLabel(bottom_section, text="Top Albums", font=('Arial', 16, 'bold'))
        albums_label.pack(side='top', padx=20, pady=20)

        self.albumsLabel = ctk.CTkLabel(bottom_section, text='', wraplength=400)
        self.albumsLabel.pack(side='top', padx=20, pady=20)

        # Right side of the main frame
        right_frame = ctk.CTkFrame(frame)
        right_frame.pack(side='right', fill='y', padx=20, pady=20)

        top_songs_label = ctk.CTkLabel(right_frame, text="Top Songs in the US", font=('Arial', 16, 'bold'))
        top_songs_label.pack(padx=20, pady=20)

        # Gets the top songs of the US
        playlist_id = '37i9dQZEVXbLp5XoPON0wI'  # Replace with the ID of your playlist
        token = get_token()
        top_songs = self.get_top_songs_of_the_playlist(token, playlist_id)
        top_songs_text = "\n".join([f'{idx + 1:2}. {song["track"]["name"]} - {", ".join([artist["name"] for artist in song["track"]["artists"]])}\n' for idx, song in enumerate(top_songs)])

        top_songs_list = ctk.CTkLabel(right_frame, text=top_songs_text, wraplength=400, anchor='nw')
        top_songs_list.pack(padx=20, pady=20)

    # Gets 25 songs from Top songs of the US playlist/ you can change this 
    def get_top_songs_of_the_playlist(self, token, playlist_id):
        url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = get_auth_header(token)
        result = get(url, headers=headers)

        if result.status_code == 200:
            try:
                playlist_data = json.loads(result.content)
                tracks = playlist_data.get('items', [])
                tracks = tracks[:25]
                return tracks
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return []
        else:
            print(f"Failed to fetch playlist. Status code: {result.status_code}")
            return []

    # performs search for artist and gets/displays top songs, albums and image if any
    def perform_search(self):
        token = get_token()
        artist_name = self.searchEntry.get()
        result = search_for_artist(token, artist_name)
        if result:
            artist_id = result['id']
            artist_images = result.get('images', [])
            image_url = artist_images[0]['url'] if artist_images else None

            songs = get_songs_by_artist(token, artist_id)
            top_songs = '\n'.join([f'{idx + 1}. {song["name"]}' for idx, song in enumerate(songs)])

            albums = get_albums_by_artist(token, artist_id)
            top_albums = '\n'.join([f'{idx + 1}. {albums["name"]}' for idx, albums in enumerate(albums)])

            self.resultLabel.configure(text=top_songs)
            self.albumsLabel.configure(text=top_albums)
        
            # Display the artist's image
            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_data = response.content
                    image = Image.open(BytesIO(image_data))
                    image = image.resize((100, 100))  
                    photo_image = ImageTk.PhotoImage(image)
                    self.artistImageLabel.configure(image=photo_image)
                    self.artistImageLabel.image = photo_image  
                else:
                    print(f"Failed to fetch image. Status code: {response.status_code}")
            else:
                print("Artist not found.")


if __name__ == '__main__':
    app = App()

    app.mainloop()

