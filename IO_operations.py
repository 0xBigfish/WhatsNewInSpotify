import json
import os.path
import pathlib
import re
from datetime import date
from os import listdir

import URI_operations


class Group(object):
    """
    A group object holds information about a group specified in the playlist_and_artists.txt file:
        1. the group id
        2. the group name
        3. the target playlist
        4. the playlist
        5. the artists
    """

    def __init__(self, group_id, group_name, target_playlist, playlist_tuples, artist_tuples):
        """
        Creates a Group object

        :param group_id: the id of the group ( in order of appearance in the .txt file, starting at 0 )
        :type group_id: int
        :param group_name: the name of the group
        :type group_name: str
        :param target_playlist: the URI of the playlist where new songs from other playlists will be added to
        :type target_playlist: str
        :param playlist_tuples: a list of playlist tuples (playlist_name, URI) that are observe by the group
        :type playlist_tuples: list[tuple[string, string]]
        :param artist_tuples: a list of artist tuples (artist_name, URI) that are observe by the group
        :type artist_tuples: list[tuple[string, string]]
        """
        self.group_id = group_id
        self.group_name = group_name
        self.target_playlist = target_playlist
        self.playlists = playlist_tuples
        self.artists = artist_tuples

    def get_group_id(self): return self.group_id

    def get_group_name(self): return self.group_name

    def get_target_playlist(self): return self.target_playlist

    def get_playlist_tuples(self): return self.playlists

    def get_artist_tuples(self): return self.artists


# ------------------------------------------------ Regular Expressions ------------------------------------------------
#
#                   Visit https://regex101.com/ for a graphical explanation of what a given RE does
#                                      (ensure to choose Python for RE semantic)
#
#
# (?P<name><subRegex>) defines a subgroup or submatch. When the main regex has a match, the substring described by
# subRegex can be easily extracted via its name using the RE's group-mechanic
#   ATTENTION: For each match by its super-regex a subgroup can only extract one match. This means that if a group COULD
# match multiple times, only the last match will be extractable, the previously matched will NOT be extractable
#
# (?:<subRegex>) is used to create groups that are NOT extractable, they have no name or ID. Mostly used when you would
# normally use parenthesis (i.e. (<regex1>\s)* matches any string that matches <regex1> or \s any amount of times)
#
# ".*" is any amount (including zero) of any characters (including whitespace) that's not a new-line character
#
# [^#"] matches any character except "#";   c is String: [^c] matches any character that is not part of c
#
# \S matches any non-whitespace character;   \s matches any whitespace character
#
_NAME_RE = "[^\s].*"
_URI_ARTIST_RE = "spotify:artist:\S*"
_URI_PLAYLIST_RE = "spotify:playlist:\S*"

_SUBGROUP_GROUP_NAME = "(?P<GROUP_NAME>.*)"
_SUBGROUP_TARGET = "## ADD_TO:{(?P<TARGET_PLAYLIST>" + _URI_PLAYLIST_RE + ")}"
_SUBGROUP_PLAYLISTS = "## PLAYLISTS={(?P<PLAYLISTS>(?:\s*" + _NAME_RE + "=" + _URI_PLAYLIST_RE + ")*)\s*}"
_SUBGROUP_ARTIST = "## ARTISTS={(?P<ARTISTS>(?:\s*" + _NAME_RE + "=" + _URI_ARTIST_RE + ")*)\s*}"

# note: a group name is NOT restricted by the playlist and artist naming standards
_GROUP_RE = "GROUP:" + _SUBGROUP_GROUP_NAME + "={\s*" \
            + _SUBGROUP_TARGET + "\s*" + _SUBGROUP_PLAYLISTS + "\s*" + _SUBGROUP_ARTIST + "\s*}"

_PLAYLIST_TUPLE_RE = _NAME_RE + "=" + _URI_PLAYLIST_RE
_ARTIST_TUPLE_RE = _NAME_RE + "=" + _URI_ARTIST_RE

# ----------------------------------------------------------------------------------------------------------------------


_NAME_OF_CONTENT_DIRECTORY = "content_files"


def read_groups_from_file():
    """
    Reads all groups from the file and returns them as a list of Group objects where group_ID starts at 0

    :return: a list of Group objects each containing a group's metadata
    :raise IndexError: when the group signature matches, but doesn't have the subgroups group_name, target_playlist,
            playlists and artists.
    """
    # TODO: change the file path to the real playlist_and_artists.txt
    # read input file
    with open("playlists_and_artists.txt", "r") as file:
        config_text = "".join(file.readlines())  # concatenates every line into a one single line

    matches = re.finditer(_GROUP_RE, config_text)
    match_list = []

    for matchNum, match in enumerate(matches, start=0):

        # check for consistency
        # each match will have 4 groups: the group name, the target playlist,the playlists and the artists.
        # group(0) is the complete match, but it's not counted by len(match.group())
        if len(match.groups()) != 4:
            raise IndexError("A match must have 4 groups, otherwise it's an illegal match! \n"
                             "\t The groups are: the group name, the target playlist, the playlists "
                             "and the artists.")

        # note: group(3) is the string containing all playlist tuples, but still contains white-space and new-line
        # chars. We use another RE to extract only the tuples (still as strings) and put them into the dictionary.
        # group(4) is the same but for the artist tuples.
        # group(0) is the complete match as a string
        #
        # we need the tuple stings to be separated into (name, URI); .split() returns a list that we cast into a tuple
        group = Group(group_id=matchNum,
                      group_name=match.group(1),
                      target_playlist=match.group(2),
                      playlist_tuples=[tuple(p_list.group(0).split("=")) for p_list in
                                       (re.finditer(_PLAYLIST_TUPLE_RE, match.group(3)))],
                      artist_tuples=[tuple(artist.group(0).split("=")) for artist in
                                     (re.finditer(_ARTIST_TUPLE_RE, match.group(4)))])

        match_list.append(group)

    return match_list


def safe_uri_content_to_hard_drive(sp, uri):
    """
    Saves the playlist's content to a file

    :param sp: the Spotify API client
    :param uri: the spotify uri of the playlist
    :type sp: spotipy.Spotify
    :type uri: str
    """

    # get current date and change the date format to yyyy.mm.dd
    today = str(date.today())  # current format: yyyy-mm-dd
    today = today.replace("-", ".")

    # rename a uri "spotify:playlist:37 ..." to "spotify_playlist_37 ..."
    uri_directory_name = uri.replace(":", "_")
    file_name = uri_directory_name + "_content_raw(" + today + ").json"

    # get main directory (all .py files are in the main directory)
    main_dir_path = os.path.dirname(__file__)  # returns the directory of this file

    # navigate to the directory containing all content file directories
    content_file_dir_path = os.path.join(main_dir_path, _NAME_OF_CONTENT_DIRECTORY)

    uri_directory_path = os.path.join(content_file_dir_path, uri_directory_name)

    # check if the needed directory already exists, if not create it
    if not os.path.isdir(uri_directory_path):
        os.mkdir(uri_directory_path)

    # get the content of the playlist and save it into a file called <uri>_content_raw(<currentDate>).json
    file_path = os.path.join(uri_directory_path, file_name)
    with open(file_path, "w") as file:
        content = sp.playlist_items(playlist_id=URI_operations.get_playlist_id_from_uri(uri))
        json.dump(content, file)
        file.close()


def read_playlists_and_artists_uris_from_file():
    """
    OBSOLETE METHOD


    Reads playlists and artists URIs from file and return them as a list of tuples: (<name>, <URI>)

    :return: a list of (name, URI) tuples
    """

    p_and_a_list = []

    # noinspection RegExpDuplicateAlternationBranch
    # a warning is thrown but this is the correct pattern !!
    # "\s*" = any number of any whitespace character
    regex = re.compile(_NAME_RE + "=\s*" + _URI_PLAYLIST_RE + "|" +
                       _NAME_RE + "=\s*" + _URI_ARTIST_RE, re.IGNORECASE)

    with open("playlists_and_artists.txt", "r") as file:
        lines = file.readlines()

    # entries must be of format: "<name> = <URI>", extract them using the regular expression
    for line in lines:
        match = regex.match(line)

        # if a part of the line matches the regex
        if match:
            name_and_uri = match.group()  # get the matched string
            tup = (name_and_uri.partition("=")[0], name_and_uri.partition("=")[2])  # split it at the "="
            p_and_a_list.append(tup)

    return p_and_a_list


def read_playlists_uris_from_file():
    """
    OBSOLETE METHOD


    Reads playlists URIs from file and return them as a list of tuples: (<name>, <URI>)

    :return: a list of (name, URI) tuples
    """

    p_and_a_list = []

    # noinspection RegExpDuplicateAlternationBranch
    # a warning is thrown but this is the correct pattern !!
    # "\s*" = any number of any whitespace character
    regex = re.compile(_NAME_RE + "=\s*" + _URI_PLAYLIST_RE, re.IGNORECASE)

    with open("playlists_and_artists.txt", "r") as file:
        lines = file.readlines()

    # entries must be of format: "<name> = <URI>", extract them using the regular expression
    for line in lines:
        match = regex.match(line)

        # if a part of the line matches the regex
        if match:
            name_and_uri = match.group()  # get the matched string
            tup = (name_and_uri.partition("=")[0], name_and_uri.partition("=")[2])  # split it at the "="
            p_and_a_list.append(tup)

    return p_and_a_list


def read_artists_uris_from_file():
    """
    OBSOLETE METHOD


    Reads artists URIs from file and return them as a list of tuples: (<name>, <URI>)

    :return: a list of (name, URI) tuples
    """

    p_and_a_list = []

    # noinspection RegExpDuplicateAlternationBranch
    # a warning is thrown but this is the correct pattern !!
    # "\s*" = any number of any whitespace character
    regex = re.compile(_NAME_RE + "=\s*" + _URI_ARTIST_RE, re.IGNORECASE)

    with open("playlists_and_artists.txt", "r") as file:
        lines = file.readlines()

    # entries must be of format: "<name> = <URI>", extract them using the regular expression
    for line in lines:
        match = regex.match(line)

        # if a part of the line matches the regex
        if match:
            name_and_uri = match.group()  # get the matched string
            tup = (name_and_uri.partition("=")[0], name_and_uri.partition("=")[2])  # split it at the "="
            p_and_a_list.append(tup)

    return p_and_a_list


def read_playlist_and_artists_names_from_file():
    """
    OBSOLETE METHOD

    Reads playlists and artists NAMES from file and return them as a list

    :return: a list of containing the name of every artist and playlist listed in the file.
    """
    names_list = []

    # noinspection RegExpDuplicateAlternationBranch
    # a warning is thrown but this is the correct pattern !!
    # "\s*" = any number of any whitespace character
    regex = re.compile(_NAME_RE + "=\s*" + _URI_PLAYLIST_RE + "|" +
                       _NAME_RE + "=\s*" + _URI_ARTIST_RE, re.IGNORECASE)

    with open("playlists_and_artists.txt", "r") as file:
        lines = file.readlines()

    # entries must be of format: "<name> = <URI>", extract them using the regular expression
    for line in lines:
        match = regex.match(line)

        # if a part of the line matches the regex
        if match:
            name_and_uri = match.group()  # get the matched string
            names_list.append(name_and_uri.partition("=")[0])  # split it at the "="

    return names_list


def find_latest_content_file(uri):
    """
    Searches for the most recently saved content file of the playlist

    :param uri: the spotify URI of the playlist / artist
    :type uri: str
    :return: the path as a pathlib.Path object. When no file was found for URI, "None" is returned
    """

    # directory structure:
    # main dir (containing all the .py files)
    #   - content_files ( =_NAME_OF_CONTENT_DIRECTORY )
    #       -spotify:playlist:<id>
    #           -spotify:playlist:<id>_content_raw_<date> (dictionary / json file)
    #           -spotify:playlist:<id>_content_raw_<date2> (dictionary / json file)
    #           ...
    #       -spotify:artist:<id>
    #           ...

    # remove ":" from uri and replace them with "_" as ":" may not be part of filename on some OS
    uri = uri.replace(":", "_")

    # get main directory (all .py files are in the main directory)
    main_dir_path = os.path.dirname(__file__)  # returns the directory of this file

    # navigate to the directory containing all content file directories
    content_file_dir_path = os.path.join(main_dir_path, _NAME_OF_CONTENT_DIRECTORY)

    # list all files and directories of the content directory (NOT recursive)
    content_overview = listdir(content_file_dir_path)

    # list all available content files for the given uri and sort them
    for directory in content_overview:
        if directory == uri and not os.path.isfile(directory):
            # find the newest / most recently saved content file
            content_files = listdir(os.path.join(content_file_dir_path, directory))
            content_files.sort()

            # because of the date format yyyy.mm.dd the newest file will be at the end of the SORTED list
            latest_content_file = content_files[len(content_files) - 1]

            # ignore the file if it is from the current day. Otherwise the method works only once a day correctly
            # content files always end with a date at the end, i.e. spotify_playlist_<id>_content_raw(2021.01.14).json
            content_file_date = latest_content_file.replace(".json", "")[-11:-1]  # gets the date
            today = str(date.today()).replace("-", ".")  # format now: yyyy.mm.dd

            if not today == content_file_date:
                # return the path to the file as a Path object (better than a String when run on different OS)
                return pathlib.Path(os.path.join(content_file_dir_path, directory, latest_content_file))

            elif len(content_files) > 1:
                # get the second most recent entry
                return pathlib.Path(
                    os.path.join(content_file_dir_path, directory, content_files[len(content_files) - 2]))

            else:
                # if there is only one content file and it's from today, act like there is no content file
                return None

    # if no content file is found, return nothing
    return None
