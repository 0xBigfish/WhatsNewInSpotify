import json

import spotipy

from IO_operations import find_latest_content_file
from IO_operations import safe_uri_content_to_hard_drive
from URI_operations import *

RELEASE_RADAR = "spotify:playlist:7I0dtpfqqtcPYNsaJn32dF"


def print_playlist_changes(sp, p_uri):
    """
    Prints the changes made to the playlist, compared to the latest content file, to the console.

    :param p_uri: the spotify uri of the playlist
    :param sp: the Spotify API client
    :type p_uri: str
    :type sp: spotipy.Spotify
    """
    # results is a json file
    # object{7}:
    #   href: https://api.spoitfy....
    #   items [number_of_items]:
    #       0 {6}:
    #           added_at: 2020-12-27T23:01:00Z
    #           added_by {5}:
    #           is_local : false
    #           primary_color : null
    #           track{19}:
    #               album{13}:
    #               artists [number_of_artists] :
    #                   0 {6}:
    #                       external_urls {1}:
    #                       href:
    #                       id:
    #                       name:
    #                       type:
    #                       uri:
    #                   1 {6}:
    #                       ...
    #               available_markets [n_of_avail_markets] :
    #               disc_number : 1
    #               duration_ms : 140026
    #               episode : false
    #               explicit : true
    #               external_ids {1}:
    #               external_urls {1}:
    #               href: https://api.spotify..
    #               id : j01u0u401
    #               is_local : false
    #               name : Lost (feat. xyz)
    #               popularity : 80
    #               preview_url : null
    #               track : true
    #               track_number : 1
    #               type : track
    #               uri : spotify:track:sjfldlksjl
    #           video_thumbnail {1} :
    #       1 {6}:
    #           .....
    #
    #   limit : 100
    #   next : null
    #   offset: 0
    #   previous: null
    #   total : 50

    # playlist_items yields a dictionary or JSON file
    results_dict = sp.playlist_items(playlist_id=get_playlist_id_from_uri(p_uri))

    # get the playlists tracks
    latest_tracks = results_dict["items"]

    # read old playlist content from file
    latest_content_file = find_latest_content_file(p_uri)
    print(latest_content_file)

    # if a content file exists for the uri:
    if latest_content_file:
        with open(latest_content_file, "r") as oldTrackFile:
            data = oldTrackFile.readline()  # only reads ONE line (json files have only one (very long) line)

            # if there is another line throw an error
            if oldTrackFile.readline() != "":
                raise TypeError("the file is empty or not a json file. Path: " + latest_content_file)

            old_results = json.loads(data)
            old_tracks = old_results["items"]

        # both are a list of dictionaries each containing the song's name and its artists names
        new_songs = []
        removed_songs = []

        # print("comparing tracks")

        # check the playlist for new songs
        for new_track in latest_tracks:
            flag_is_new_song = True
            for old_track in old_tracks:
                # if the current track matches with a track in the old list, then it's not a new song
                if new_track["track"]["uri"] == old_track["track"]["uri"]:
                    flag_is_new_song = False
                    break

            if flag_is_new_song:
                song_info = {"name": new_track["track"]["name"],
                             "artists": new_track["track"]["artists"]}
                new_songs.append(song_info)

        # check the playlist for removed songs
        for old_track in old_tracks:
            flag_was_removed = True
            for new_track in latest_tracks:
                if old_track["track"]["name"] == new_track["track"]["name"]:
                    flag_was_removed = False
                    break

            if flag_was_removed:
                song_info = {"name": old_track["track"]["name"],
                             "artists": old_track["track"]["artists"]}
                removed_songs.append(song_info)

        print("-------------------------- New Songs: --------------------------")
        for song in new_songs:
            artists = ""
            n_of_artists = len(song["artists"])

            for i in range(0, n_of_artists - 1):
                artists += song["artists"][i]["name"] + ", "
            artists += song["artists"][n_of_artists - 1]["name"]

            print(song["name"] + " - " + artists)

        print("------------------------ Removed Songs: ------------------------")
        for song in removed_songs:

            artists = ""
            n_of_artists = len(song["artists"])

            for i in range(0, n_of_artists - 1):
                artists += song["artists"][i]["name"] + ", "
            artists += song["artists"][n_of_artists - 1]["name"]

            print(song["name"] + " - " + artists)
    else:
        print("------------------- No data for playlist yet -------------------")


def get_all_songs_from_playlist(sp, p_uri):
    """
    returns a list containing the song uri of each song in the playlist

    if no content file is found for the playlist, a new content file is created.

    :param p_uri: the spotify uri of the playlist
    :param sp: the Spotify API client
    :type p_uri: str
    :type sp: spotipy.Spotify
    :raise TypeError: the content file is not a json file.
    :return a list of every song's uri in the playlist
    """
    # results is a json file
    # object{7}:
    #   href: https://api.spoitfy....
    #   items [number_of_items]:
    #       0 {6}:
    #           added_at: 2020-12-27T23:01:00Z
    #           added_by {5}:
    #           is_local : false
    #           primary_color : null
    #           track{19}:
    #               album{13}:
    #               artists [number_of_artists] :
    #                   0 {6}:
    #                       external_urls {1}:
    #                       href:
    #                       id:
    #                       name:
    #                       type:
    #                       uri:
    #                   1 {6}:
    #                       ...
    #               available_markets [n_of_avail_markets] :
    #               disc_number : 1
    #               duration_ms : 140026
    #               episode : false
    #               explicit : true
    #               external_ids {1}:
    #               external_urls {1}:
    #               href: https://api.spotify..
    #               id : j01u0u401
    #               is_local : false
    #               name : Lost (feat. xyz)
    #               popularity : 80
    #               preview_url : null
    #               track : true
    #               track_number : 1
    #               type : track
    #               uri : spotify:track:sjfldlksjl
    #           video_thumbnail {1} :
    #       1 {6}:
    #           .....
    #
    #   limit : 100
    #   next : null
    #   offset: 0
    #   previous: null
    #   total : 50
    # playlist_items yields a dictionary or JSON file
    results_dict = sp.playlist_items(playlist_id=get_playlist_id_from_uri(p_uri))

    # get the playlists tracks
    latest_tracks = results_dict["items"]

    return [new_track["track"]["uri"] for new_track in latest_tracks]


def get_new_songs_in_playlist(sp, p_uri):
    """
    songs that have newly been added to this playlist will be added to the release radar.

    if no content file is found for the playlist, a new content file is created.

    :param p_uri: the spotify uri of the playlist
    :param sp: the Spotify API client
    :type p_uri: str
    :type sp: spotipy.Spotify
    :return a list containing all new songs in the playlist
    """
    # read old playlist content from file
    latest_content_file = find_latest_content_file(p_uri)

    # if a content file exists for the uri:
    if latest_content_file:

        # get the uris of the songs currently in the playlist
        song_uris_in_playlist = get_all_songs_from_playlist(sp, p_uri)

        with open(latest_content_file, "r") as old_track_file:
            data = old_track_file.readline()  # only reads ONE line (json files have only one (very long) line)

            # if there is another line throw an error
            if old_track_file.readline() != "":
                raise TypeError("The content file is not a json file. Json files have only one (very long) line.")

            old_results = json.loads(data)
            old_tracks_uris = [song_data["track"]["uri"] for song_data in old_results["items"]]

        # check the playlist for new songs by check whether they were already in the old content_file or not
        new_songs = [song for song in song_uris_in_playlist if not old_tracks_uris.__contains__(song)]

        # remove duplicate entries using list comprehension
        song_uris = [s for n, s in enumerate(new_songs) if s not in new_songs[:n]]

        return song_uris

    else:
        # if there are no records of the playlist yet, create the first record
        safe_uri_content_to_hard_drive(sp, p_uri)
        return []


def create_new_private_playlist(sp, name):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    creates a new playlist called <name> for the user that is currently logged in

    :param sp: the Spotify API client
    :param name: what the playlist will be named
    :type sp: spotipy.Spotify
    :type name: str
    """
    sp.user_playlist_create(user=sp.current_user()["id"], name=name, public=False)


def add_song_to_playlist(sp, playlist_uri, song_uri):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    adds a song to a playlist

    :param sp: the Spotify API client
    :param song_uri: the uri of the song that will be added
    :param playlist_uri: the uri of the playlist that the song will be added to
    :type sp: spotipy.Spotify
    :type song_uri: str
    :type playlist_uri: str
    """
    playlist_id = get_playlist_id_from_uri(playlist_uri)
    sp.playlist_add_items(playlist_id, [song_uri])


def add_songs_to_playlist(sp, playlist_uri, song_uris):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    adds multiple songs to a playlist

    :param sp: the Spotify API client
    :param song_uris: the list of uris of the songs that will be added
    :param playlist_uri: the uri of the playlist that the song will be added to
    :type sp: spotipy.Spotify
    :type song_uris: list
    :type playlist_uri: str
    """
    # an error occurs when trying to add an emtpy list of songs to the playlist
    if len(song_uris) > 1:
        playlist_id = get_playlist_id_from_uri(playlist_uri)
        sp.playlist_add_items(playlist_id, song_uris)


def remove_song_from_playlist(sp, playlist_uri, song_uri):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    removes all occurrences of the song in the playlist

    :param sp: the Spotify API client
    :param song_uri: the uri of the song that will be removed
    :param playlist_uri: the uri of the playlist that the song will be removed from
    :type sp: spotipy.Spotify
    :type song_uri: str
    :type playlist_uri: str
    """
    playlist_id = get_playlist_id_from_uri(playlist_uri)
    sp.playlist_remove_all_occurrences_of_items(playlist_id, [song_uri])


def remove_songs_from_playlist(sp, playlist_uri, song_uris):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    removes all occurrences of the songs in the playlist

    :param sp: the Spotify API client
    :param song_uris: the list of uris of the song that will be removed
    :param playlist_uri: the uri of the playlist that the songs will be removed from
    :type sp: spotipy.Spotify
    :type song_uris: list
    :type playlist_uri: str
    """
    # an error occurs when trying to remove an empty list of songs from the playlist
    if len(song_uris) > 1:
        playlist_id = get_playlist_id_from_uri(playlist_uri)
        sp.playlist_remove_all_occurrences_of_items(playlist_id, song_uris)


def remove_duplicate_songs_from_playlist(sp, playlist_uri):
    """
    ! REQUIRES LOGIN TO SPOTIFY !

    removes all duplicates of all songs in the playlist; only the OLDEST entry of a song will remain

    :param sp: the Spotify API client
    :param playlist_uri: the uri of the playlist that the songs will be removed from
    :type sp: spotipy.Spotify
    :type playlist_uri: str
    """
    p_id = get_playlist_id_from_uri(playlist_uri)

    # see get_all_songs_from_playlist() for a more detailed documentation of results_dict (json file)
    results_dict = sp.playlist_items(p_id)
    song_uris = [results_dict["items"][i]["track"]["uri"] for i in range(0, len(results_dict["items"]))]
    items_to_remove = []

    # important: j starts at i+1
    for i in range(0, len(song_uris)):
        duplicates_indices = []
        for j in range(i+1, len(song_uris)):
            # if a song occurs multiple times
            if song_uris[i] == song_uris[j]:
                duplicates_indices.append(j)

        # there are multiple occurrences of the song
        if len(duplicates_indices) > 0:
            # data is the format the spotipy library expects when calling playlist_remove_specific_occurrences_of_items
            data = {"uri": get_song_id_from_uri(song_uris[i]),
                    "positions": duplicates_indices}
            items_to_remove.append(data)

    # for performance reasons, do not send a request if there are no songs to be removed
    if len(items_to_remove) > 0:
        sp.playlist_remove_specific_occurrences_of_items(p_id, items_to_remove)
